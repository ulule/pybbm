from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from guardian.models import UserObjectPermission as BaseUserObjectPermission
from guardian.managers import UserObjectPermissionManager as BaseUserObjectPermissionManager
from guardian.exceptions import ObjectNotPersisted


class UserObjectPermissionManager(BaseUserObjectPermissionManager):
    def assign(self, permission, user, obj, ctype=None):
        """
        Assigns permission with given ``perm`` for an instance ``obj`` and
        ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first" % obj)

        if not ctype:
            ctype = ContentType.objects.get_for_model(obj)

        if not isinstance(permission, Permission):
            permission = Permission.objects.get(content_type=ctype, codename=permission)

        obj_perm, created = self.get_or_create(
            content_type=ctype,
            permission=permission,
            object_pk=obj.pk,
            user=user)
        return obj_perm

    def remove_perm(self, perm, user, obj, ctype=None):
        """
        Removes permission ``perm`` for an instance ``obj`` and given ``user``.
        """
        if getattr(obj, 'pk', None) is None:
            raise ObjectNotPersisted("Object %s needs to be persisted first" % obj)

        if not ctype:
            ctype = ContentType.objects.get_for_model(obj)

        (self.filter(permission__codename=perm,
                     user=user,
                     object_pk=obj.pk,
                     content_type=ctype)
         .delete())


class UserObjectPermission(BaseUserObjectPermission):
    objects = UserObjectPermissionManager()

    class Meta:
        proxy = True
