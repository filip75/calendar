from rest_framework.views import APIView


def clean_permissions(view: APIView):
    view.permission_classes = []
    return view
