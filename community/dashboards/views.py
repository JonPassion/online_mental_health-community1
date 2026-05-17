
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

@login_required
def user_dashboard(request):
    return render(request, 'dashboards/user_dashboard.html')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')
