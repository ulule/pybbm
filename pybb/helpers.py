def load_user_posts(qs, user):
    for post in qs:
        post.user = user

        if post.topic.user_id == user.pk:
            post.topic.user = user

    return qs
