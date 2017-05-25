DJANGO_MAX_BATCH_SIZE = 1000

# Slugs

GROUP_STAGING_SLUG = 'group_staging'
USER_STAGING_SLUG = 'user_staging'
DOMAIN_STAGING_SLUG = 'domain_staging'
LOCATION_STAGING_SLUG = 'location_staging'
FORM_STAGING_SLUG = 'form_staging'
SYNCLOG_STAGING_SLUG = 'synclog_staging'

USER_DIM_SLUG = 'user_dim'
GROUP_DIM_SLUG = 'group_dim'
LOCATION_DIM_SLUG = 'location_dim'
DOMAIN_DIM_SLUG = 'domain_dim'
USER_LOCATION_DIM_SLUG = 'user_location_dim'
USER_GROUP_DIM_SLUG = 'user_group_dim'

APP_STATUS_FACT_SLUG = 'app_status_fact'

DIM_TABLES = [
    GROUP_STAGING_SLUG,
    USER_STAGING_SLUG,
    DOMAIN_STAGING_SLUG,
    LOCATION_STAGING_SLUG,
    FORM_STAGING_SLUG,
    SYNCLOG_STAGING_SLUG,
]

FACT_TABLES = [
    APP_STATUS_FACT_SLUG,
]
