from __future__ import absolute_import
import json
import uuid
from functools import partial
from six.moves.urllib.parse import urlencode
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from corehq import toggles
from corehq.apps.app_manager import add_ons
from corehq.apps.app_manager.dbaccessors import get_app, wrap_app, get_apps_in_domain
from corehq.apps.app_manager.decorators import require_deploy_apps
from corehq.apps.app_manager.exceptions import AppEditingError, \
    ModuleNotFoundException, FormNotFoundException, RemoteRequestError, AppLinkError, ActionNotPermitted, \
    RemoteAuthError
from corehq.apps.app_manager.models import Application, ReportModule, enable_usercase_if_necessary, CustomIcon
from corehq.apps.app_manager.remote_link_accessors import pull_missing_multimedia_from_remote

from corehq.apps.app_manager.util import update_form_unique_ids
from corehq.apps.userreports.exceptions import BadSpecError
from corehq.apps.userreports.util import get_static_report_mapping
from corehq.util.couch import DocumentNotFound
import six

CASE_TYPE_CONFLICT_MSG = (
    "Warning: The form's new module "
    "has a different case type from the old module.<br />"
    "Make sure all case properties you are loading "
    "are available in the new case type"
)


@require_deploy_apps
def back_to_main(request, domain, app_id=None, module_id=None, form_id=None,
                 form_unique_id=None, module_unique_id=None):
    """
    returns an HttpResponseRedirect back to the main page for the App Manager app
    with the correct GET parameters.

    This is meant to be used by views that process a POST request,
    which then redirect to the main page.

    """
    page = None
    params = {}
    args = [domain]
    view_name = 'default_app'

    form_view = 'form_source'

    if app_id is not None:
        view_name = 'view_app'
        args.append(app_id)

        app = get_app(domain, app_id)

        module = None
        try:
            if module_id is not None:
                module = app.get_module(module_id)
            elif module_unique_id is not None:
                module = app.get_module_by_unique_id(module_unique_id)
        except ModuleNotFoundException:
            raise Http404()

        form = None
        if form_id is not None and module is not None:
            try:
                form = module.get_form(form_id)
            except IndexError:
                raise Http404()
        elif form_unique_id is not None:
            try:
                form = app.get_form(form_unique_id)
            except FormNotFoundException:
                raise Http404()

        if form is not None:
            view_name = 'view_form' if form.no_vellum else form_view
            args.append(form.unique_id)
        elif module is not None:
            view_name = 'view_module'
            args.append(module.unique_id)

    if page:
        view_name = page

    return HttpResponseRedirect(
        "%s%s" % (
            reverse(view_name, args=args),
            "?%s" % urlencode(params) if params else ""
        )
    )


def get_langs(request, app):
    lang = request.GET.get(
        'lang',
        request.COOKIES.get('lang', app.langs[0] if hasattr(app, 'langs') and app.langs else '')
    )
    langs = None
    if app and hasattr(app, 'langs'):
        if not app.langs and not app.is_remote_app:
            # lots of things fail if the app doesn't have any languages.
            # the best we can do is add 'en' if there's nothing else.
            app.langs.append('en')
            app.save()
        if not lang or lang not in app.langs:
            lang = (app.langs or ['en'])[0]
        langs = [lang] + app.langs
    return lang, langs


def bail(request, domain, app_id, not_found=""):
    if not_found:
        messages.error(request, 'Oops! We could not find that %s. Please try again' % not_found)
    else:
        messages.error(request, 'Oops! We could not complete your request. Please try again')
    return back_to_main(request, domain, app_id)


def encode_if_unicode(s):
    return s.encode('utf-8') if isinstance(s, six.text_type) else s


def validate_langs(request, existing_langs):
    o = json.loads(request.body)
    langs = o['langs']
    rename = o['rename']

    assert set(rename.keys()).issubset(existing_langs)
    assert set(rename.values()).issubset(langs)
    # assert that there are no repeats in the values of rename
    assert len(set(rename.values())) == len(list(rename.values()))
    # assert that no lang is renamed to an already existing lang
    for old, new in rename.items():
        if old != new:
            assert(new not in existing_langs)

    return (langs, rename)


def get_blank_form_xml(form_name):
    return render_to_string("app_manager/blank_form.xml", context={
        'xmlns': str(uuid.uuid4()).upper(),
        'name': form_name,
    })


def overwrite_app(app, master_build, report_map=None):
    excluded_fields = set(Application._meta_fields).union([
        'date_created', 'build_profiles', 'copy_history', 'copy_of',
        'name', 'comment', 'doc_type', '_LAZY_ATTACHMENTS', 'practice_mobile_worker_id'
    ])
    master_json = master_build.to_json()
    app_json = app.to_json()
    id_map = _get_form_id_map(app_json)  # do this before we change the source

    for key, value in six.iteritems(master_json):
        if key not in excluded_fields:
            app_json[key] = value
    app_json['version'] = master_json['version']
    wrapped_app = wrap_app(app_json)
    for module in wrapped_app.modules:
        if isinstance(module, ReportModule):
            if report_map is not None:
                for config in module.report_configs:
                    try:
                        config.report_id = report_map[config.report_id]
                    except KeyError:
                        raise AppEditingError('Dynamic UCR used in linked app')
            else:
                raise AppEditingError('Report map not passed to overwrite_app')

    wrapped_app = _update_form_ids(wrapped_app, master_build, id_map)
    enable_usercase_if_necessary(wrapped_app)
    return wrapped_app


def _get_form_id_map(app):
    id_map = {}
    for module in app['modules']:
        for form in module['forms']:
            id_map[form['xmlns']] = form['unique_id']
    return id_map


def _update_form_ids(app, master_app, id_map):

    _attachments = master_app.get_attachments()

    app_source = app.to_json()
    app_source.pop('external_blobs')
    app_source['_attachments'] = _attachments

    updated_source = update_form_unique_ids(app_source, id_map)

    attachments = app_source.pop('_attachments')
    new_wrapped_app = wrap_app(updated_source)
    save = partial(new_wrapped_app.save, increment_version=False)
    return new_wrapped_app.save_attachments(attachments, save)


def get_practice_mode_configured_apps(domain, mobile_worker_id=None):

    def is_set(app_or_profile):
        if mobile_worker_id:
            if app_or_profile.practice_mobile_worker_id == mobile_worker_id:
                return True
        else:
            if app_or_profile.practice_mobile_worker_id:
                return True

    def _practice_mode_configured(app):
        if is_set(app):
            return True
        return any(is_set(profile) for _, profile in app.build_profiles.items())

    return [app for app in get_apps_in_domain(domain) if _practice_mode_configured(app)]


def unset_practice_mode_configured_apps(domain, mobile_worker_id=None):
    """
    Unset practice user for apps that have a practice user configured directly or
    on a build profile of apps in the domain. If a mobile_worker_id is specified,
    only apps configured with that user will be unset

    returns:
        list of apps on which the practice user was unset

    kwargs:
        mobile_worker_id: id of mobile worker. If this is specified, only those apps
        configured with this mobile worker will be unset. If not, apps that are configured
        with any mobile worker are unset
    """

    def unset_user(app_or_profile):
        if mobile_worker_id:
            if app_or_profile.practice_mobile_worker_id == mobile_worker_id:
                app_or_profile.practice_mobile_worker_id = None
        else:
            if app_or_profile.practice_mobile_worker_id:
                app_or_profile.practice_mobile_worker_id = None

    apps = get_practice_mode_configured_apps(domain, mobile_worker_id)
    for app in apps:
        unset_user(app)
        for _, profile in six.iteritems(app.build_profiles):
            unset_user(profile)
        app.save()

    return apps


def handle_custom_icon_edits(request, form_or_module, lang):
    if toggles.CUSTOM_ICON_BADGES.enabled(request.domain):
        icon_text_body = request.POST.get("custom_icon_text_body")
        icon_xpath = request.POST.get("custom_icon_xpath")
        icon_form = request.POST.get("custom_icon_form")

        # if there is a request to set custom icon
        if icon_form:
            # validate that only of either text or xpath should be present
            if (icon_text_body and icon_xpath) or (not icon_text_body and not icon_xpath):
                return _("Please enter either text body or xpath for custom icon")

            # a form should have just one custom icon for now
            # so this just adds a new one with params or replaces the existing one with new params
            form_custom_icon = (form_or_module.custom_icon if form_or_module.custom_icon else CustomIcon())
            form_custom_icon.form = icon_form
            form_custom_icon.text[lang] = icon_text_body
            form_custom_icon.xpath = icon_xpath

            form_or_module.custom_icons = [form_custom_icon]

        # if there is a request to unset custom icon
        if not icon_form and form_or_module.custom_icon:
            form_or_module.custom_icons = []


def update_linked_app(app):
    try:
        master_version = app.get_master_version()
    except RemoteRequestError:
        raise AppLinkError(_(
            'Unable to pull latest master from remote CommCare HQ. Please try again later.'
        ))

    if master_version > app.version:
        try:
            latest_master_build = app.get_latest_master_release()
        except ActionNotPermitted:
            raise AppLinkError(_(
                'This project is not authorized to update from the master application. '
                'Please contact the maintainer of the master app if you believe this is a mistake. '
            ))
        except RemoteAuthError:
            raise AppLinkError(_(
                'Authentication failure attempting to pull latest master from remote CommCare HQ.'
                'Please verify your authentication details for the remote link are correct.'
            ))
        except RemoteRequestError:
            raise AppLinkError(_(
                'Unable to pull latest master from remote CommCare HQ. Please try again later.'
            ))

        try:
            report_map = get_static_report_mapping(latest_master_build.domain, app['domain'], {})
        except (BadSpecError, DocumentNotFound) as e:
            raise AppLinkError(_('This linked application uses mobile UCRs '
                                 'which are available in this domain: %(message)s') % {'message': e})

        try:
            app = overwrite_app(app, latest_master_build, report_map)
        except AppEditingError:
            raise AppLinkError(_('This linked application uses dynamic mobile UCRs '
                                 'which are currently not supported. For this application '
                                 'to function correctly, you will need to remove those modules '
                                 'or revert to a previous version that did not include them.'))

    if app.master_is_remote:
        try:
            pull_missing_multimedia_from_remote(app)
        except RemoteRequestError:
            raise AppLinkError(_(
                'Error fetching multimedia from remote server. Please try again later.'
            ))
