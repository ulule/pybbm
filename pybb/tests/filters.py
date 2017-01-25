def premoderate(user, data):
    """
    Test premoderate function
    Allow post without moderation for staff users only
    """
    return user.is_staff
