from rest_framework.decorators import action
from django.db.models import *
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from loan.models import *
from loan.serializers import *


class LoanCRUDView(ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONOpenAPIRenderer]
    @action(methods=["post"], detail=False, url_path="create", url_name="loan_create")
    def loan_create(self, request):
        data = request.data
        data['user'] = request.user.id

        mortgage = False if request.data.get('loan_type', None) != 'Mortgage' else True
        loan = False if request.data.get('loan_type', None) != 'Loan' else True
        other = False if request.data.get('loan_type', None) != 'Other' else True
        installment = False if request.data.get('loan_type', None) != 'Installment' else True

        if mortgage:
            if not data.get('down_payment', False) or not data.get('property_value', False):
                return Response({'error': 'down_payment and property_value required in this type'},
                                status=status.HTTP_400_BAD_REQUEST)

        elif loan:
            if data.get('down_payment', False) or data.get('property_value', False):
                return Response({'error': 'down_payment or property_value must`t be in this type'},
                                status=status.HTTP_400_BAD_REQUEST)

        elif other:
            if data.get('down_payment', False) or data.get('property_value', False) \
                    or data.get('loan_term', False) or data.get('monthly_payment', False) or data.get('interest_rate',
                                                                                                      False):
                return Response({'error': f'{('down_payment', 'property_value',
                                      'loan_term', 'monthly_payment', 'interest_rate')} must`t be in this type'},
                                status=status.HTTP_400_BAD_REQUEST)

        elif installment:
            if data.get('down_payment', False) or data.get('property_value', False) \
                    or data.get('interest_rate', False):
                return Response({'error': f'{('down_payment', 'property_value', 'interest_rate')} '
                                          f'must`t be in this type'},
                                status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({
                'error': 'Please provide either correct loan_type',
                'example': 'Mortgage, Loan, Other, Installment'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoanCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @action(methods=["post"], detail=False, url_path="list", url_name="loan_list")
    def loan_list(self, request):
        serializer = LoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        date_start = serializer.validated_data.get('date_start')
        date_end = serializer.validated_data.get('date_end')
        loan_type = serializer.validated_data.get('loan_type')

        if not date_start or not date_end:
            queryset = MainLoan.objects.filter(loan_type__in=loan_type,
                                               user=user)

            queryset = LoanSerializer(queryset, many=True).data

            return Response(queryset, status=status.HTTP_200_OK)

        queryset = MainLoan.objects.filter(loan_type__in=loan_type,
                                           loan_insurance__gte=date_start,
                                           loan_insurance__lte=date_end,
                                           user=user)

        queryset = LoanSerializer(queryset, many=True).data

        return Response(queryset, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False, url_path="delete", url_name="loan_delete")
    def loan_delete(self, request):
        serializer = LoanDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan_ids = serializer.validated_data.get('loan_list')
        user = request.user
        if loan_ids:
            try:
                for loan_id in loan_ids:
                    obj = get_object_or_404(MainLoan, id=loan_id, user=user)
                    obj.delete()
            except Exception:
                return Response({'message': 'id or user dose not exist'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': f'{len(loan_ids)} operations was deleted'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'something went wrong try again later'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["patch"], detail=True, url_path="update", url_name="loan_update")
    def loan_update(self, request, pk=None):
        obj = get_object_or_404(MainLoan, id=pk, user=request.user)
        serializer = LoanUpdateSerializer(instance=obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="icons", url_name="icons")
    def icon(self, request):
        obj = LoanSVG.objects.all().values()
        return Response({'svg': obj}, status=status.HTTP_200_OK)

