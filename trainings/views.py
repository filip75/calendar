from django.shortcuts import redirect, render


def home(request):
    if not request.user.is_authenticated:
        return redirect('users-login')

    return render(request, 'trainings/home.html')
