function(doc) {
    //basic emission of itemized audit events
    if (doc.base_type == 'AuditEvent') {
        //by class of audit event
        emit(doc.event_class, null);

        //by username, and the events they do
        emit([doc.user, doc.event_class], null);

        if (doc.event_class == "ModelActionAudit") {
            emit(['ModelActionAudit', doc.object_type, doc.object_uuid], doc.revision_id);
        }
    }
}