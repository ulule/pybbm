from celery.task import task


@task
def generate_markup(post_id):
    from pybb.models import Post

    logger = generate_markup.get_logger()

    post = Post.objects.get(pk=post_id)
    post.render(commit=True)

    logger.info('Text generated for %r' % post)


@task
def sync_cover(topic_id):
    from pybb.models import Topic

    logger = sync_cover.get_logger()

    topic = Topic.objects.get(pk=topic_id)
    topic.sync_cover()

    logger.info('Syncing cover for %r' % topic)
