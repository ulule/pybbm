from celery.task import task

from django.db import connection, transaction
from django.utils.html import strip_tags

from pybb.processors import markup


@task
def generate_markup(table_name, primary_key, pk, body):
    logger = generate_markup.get_logger()

    cursor = connection.cursor()

    body_html = markup(body)

    body_text = strip_tags(body_html)

    cursor.execute('UPDATE ' + table_name + ' SET body_html = %s, body_text = %s WHERE ' + primary_key + ' = %s', [
        body_html,
        body_text,
        pk
    ])

    transaction.commit_unless_managed()

    logger.info('Text generated for %s %s=%s' % (table_name, primary_key, pk))
