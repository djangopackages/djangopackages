from django.db import connections, DEFAULT_DB_ALIAS, transaction
from django.core.management.color import no_style


def reset_sequences(*models):
    """
    After loading data the sequences must be reset in the database if
    the primary keys are manually specified. This is handled
    automatically by django for fixtures.

    Much of this is modeled after django.core.management.commands.loaddata.
    """
    # connection = connections[DEFAULT_DB_ALIAS]
    # cursor = connection.cursor()
    # sequence_sql = connection.ops.sequence_reset_sql(no_style(), models)
    # if sequence_sql:
    #     for line in sequence_sql:
    #         cursor.execute(line)
    # # transaction.commit_unless_managed()
    # cursor.close()
    pass
