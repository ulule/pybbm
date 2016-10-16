from pybb.models.base import BasePoll, BasePollAnswer, BasePollAnswerUser, PollAnswerUserManager


class Poll(BasePoll):
    class Meta(BasePoll.Meta):
        abstract = False


class PollAnswer(BasePollAnswer):
    class Meta(BasePollAnswer.Meta):
        abstract = False


class PollAnswerUser(BasePollAnswerUser):
    class Meta(BasePollAnswerUser.Meta):
        abstract = False

    objects = PollAnswerUserManager()
