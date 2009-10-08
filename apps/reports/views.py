from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect

from rapidsms.webui.utils import render_to_response

from transformers.csv import format_csv 
from models import Case, SqlReport
from xformmanager.models import FormDefModel
from hq.models import ExtUser
from hq.utils import paginate
from hq.decorators import extuser_required

import util

from StringIO import StringIO
from transformers.csv import UnicodeWriter

@extuser_required()
def reports(request, template_name="list.html"):
    # not sure where this view will live in the UI yet
    context = {}
    extuser = request.extuser
    context['domain'] = extuser.domain
    context['case_reports'] = Case.objects.filter(domain=extuser.domain)
    context['sql_reports'] = SqlReport.objects.filter(domain=extuser.domain)
    report_module = util.get_custom_report_module(extuser.domain)
    if report_module:
        custom = util.get_custom_reports(report_module)
        context['custom_reports'] = custom
    else:
        context['custom_reports'] = None
    if not context['custom_reports'] and not context['sql_reports']\
       and not context['case_reports']:
        return render_to_response(request, 
                                  "domain_not_found.html",
                                  context)
    return render_to_response(request, template_name, context)

@extuser_required()
def case_flat(request, case_id, template_name="case_flat.html"):
    '''A flat view of the topmost data for all cases'''
    context = {}
    extuser = request.extuser
    case = Case.objects.get(id=case_id)
    
    context['cols'] = case.get_column_names()
    
    data = case.get_topmost_data()
    keys = data.keys()
    keys.sort()
    flattened = []
    for key in keys:
        flattened.append(data[key])
    
    
    context['data'] = paginate(request, flattened)    
    context['case'] = case
    
    return render_to_response(request, template_name, context)

    
@extuser_required()
def single_case_view(request, case_id, case_instance_id, template_name="single_case.html"):
    '''View for all of a single case's data, broken down by form.'''
    context = {}
    extuser = request.extuser
    
    case = Case.objects.get(id=case_id)
    data = case.get_data_for_case(case_instance_id)
    
    context['case_instance_id'] = case_instance_id
    context['case_data'] = data
    context['case'] = case
    
    return render_to_response(request, template_name, context)

@extuser_required()
def case_export_csv(request, case_id):
    case = Case.objects.get(id=case_id)
    cols = case.get_column_names()
    data = case.get_topmost_data().values()
    output = StringIO()
    w = UnicodeWriter(output)
    w.writerow(cols)
    for row in data:
        w.writerow(row)
    output.seek(0)
    response = HttpResponse(output.read(),
                        mimetype='application/ms-excel')
    response["content-disposition"] = 'attachment; filename="%s-%s.csv"' % ( case.name, str(datetime.now().date()))
    return response


@extuser_required()
def custom_report(request, domain_id, report_name):
    context = {}
    extuser = request.extuser
    context["domain"] = extuser.domain
    context["report_name"] = report_name
    report_module = util.get_custom_report_module(extuser.domain)
    if not report_module:
        return render_to_response(request, 
                                  "domain_not_found.html",
                                  context)
    if not hasattr(report_module, report_name):
        return render_to_response(request, 
                                  "custom/report_not_found.html",
                                  context)
    report_method = getattr(report_module, report_name)
    context["report_display"] = report_method.__doc__
    context["report_body"] = report_method(request)
    return render_to_response(request, "custom/base.html", context)

@extuser_required()
def sql_report(request, report_id, template_name="sql_report.html"):
    '''View a single sql report.'''
    extuser = request.extuser
    report = SqlReport.objects.get(id=report_id)
    whereclause = _get_whereclause(request.GET)
    table = report.to_html_table({"whereclause": whereclause})
    return render_to_response(request, template_name, {"report": report, "table": table})

@extuser_required()
def sql_report_csv(request, report_id):
    '''View a single sql report.'''
    extuser = request.extuser
    report = SqlReport.objects.get(id=report_id)
    whereclause = _get_whereclause(request.GET)
    cols, data = report.get_data({"whereclause": whereclause})
    return format_csv(data, cols, report.title)
    

def _get_whereclause(params):
    """Given a dictionary of params {key1: val1, key2: val2 } 
       return a partial query like:
       WHERE key1 = val1
       AND   key2 = val2
    """
    query_parts = []
    first = False
    for key, val in params.items():
        if not first:
            first = True
            query_parts.append("WHERE %s = '%s'" % (key, val))
        else:
            query_parts.append("AND %s = '%s'" % (key, val))
    return " ".join(query_parts)