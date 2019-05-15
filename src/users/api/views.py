from rest_framework import views, generics
from rest_framework import permissions, status
from rest_framework.response import Response

from .serializers import RegistrationSerializer, UserSerializer


class UserDetailView(views.APIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status.HTTP_200_OK)


class RegistrationAPI(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)
