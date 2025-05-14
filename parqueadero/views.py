from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Reserva, Parqueadero, EspacioParqueadero
from .serializers import ReservaSerializer

class CrearReservaView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # Usuario autenticado

        serializer = ReservaSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(id_usuario=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
