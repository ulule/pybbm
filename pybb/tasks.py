from celery.task import task


@task
def generate_markup(post_id):
    from pybb.models import Post

    logger = generate_markup.get_logger()

    Post.objects.get(pk=post_id).render(commit=True)

    logger.info('Text generated for Post[pk=%s]' % post_id)


@task
def sync_cover(topic_id):
    from pybb.models import Topic

    logger = sync_cover.get_logger()

    Topic.objects.get(pk=topic_id).sync_cover()

    logger.info('Syncing cover for Topic[pk=%s]' % topic_id)
