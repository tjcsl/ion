from rest_framework import serializers


class UserListSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()

    def restore_object(self, attrs, instance=None):
        """
        Given a dictionary of deserialized field values, either update
        an existing model instance, or create a new model instance.
        """
        if instance is not None:
            instance.email = attrs.get('email', instance.email)
            instance.content = attrs.get('content', instance.content)
            instance.created = attrs.get('created', instance.created)
            return instance
        return Comment(**attrs)