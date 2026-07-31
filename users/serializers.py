from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from .models import CustomUser

class SignUpSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['id','username','email','password','first_name','last_name','address','age']
        read_only_fields = ['id']

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class SignUpResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = SignUpSerializer()
