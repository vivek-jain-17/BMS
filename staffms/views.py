# staffms/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from .forms import StaffCreationForm
from django.shortcuts import render, redirect, get_object_or_404 # get_object_or_404 add kiya
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from taskms.models import Task  # Naya import
from .forms import StaffCreationForm
from accounts.decorators import role_required


@login_required
@role_required(['admin', 'owner', 'ceo'])
def staff_list(request):
    # Security: Only fetch users belonging to the logged-in user's company
    company = request.user.company
    if not company:
        messages.error(request, "You must be assigned to a company to view staff.")
        return redirect('dashboard:home')

    # Exclude the current logged-in user from the list if you want, or show everyone
    staff_members = User.objects.filter(company=company).order_by('-created_at')

    context = {
        'staff_members': staff_members,
        'page_title': 'Staff Directory'
    }
    if request.headers.get('HX-Request'):
        # Sirf content bhejo, base layout nahi
        return render(request, 'staffms/partials/staff_list_content.html', context) 
    
    # Normal load ke liye pura page
    return render(request, 'staffms/staff_list.html', context)

@login_required
def add_staff(request):
    if not request.user.company:
        messages.error(request, "You need a company to add staff.")
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            # Don't save to DB immediately
            new_staff = form.save(commit=False)
            
            # Automatically assign them to the boss's company
            new_staff.company = request.user.company
            
            # Set a default password (they can change it later)
            new_staff.set_password('Welcome@123') 
            new_staff.is_staff = True # Django's built in flag
            
            new_staff.save()
            messages.success(request, f"Successfully added {new_staff.first_name} to the team.")
            return redirect('staffms:staff_list')
    else:
        form = StaffCreationForm()

    context = {
        'form': form,
        'page_title': 'Add New Employee'
    }
    return render(request, 'staffms/add_staff.html', context)


@login_required
def staff_profile(request, user_id):
    # 1. Jis staff member pe click kiya hai, usko fetch karo
    # UUIDField use kar rahe ho, toh user_id ko match karenge
    staff_member = get_object_or_404(User, user_id=user_id, company=request.user.company)
    
    # 2. Uske assigned tasks nikal lo
    staff_tasks = Task.objects.filter(assigned_to=staff_member).order_by('-created_at')
    
    # 3. Analytics calculate karo
    stats = {
        'total': staff_tasks.count(),
        'pending': staff_tasks.filter(status='pending').count(),
        'in_progress': staff_tasks.filter(status='in_progress').count(),
        'completed': staff_tasks.filter(status='completed').count(),
    }

    # HTMX Dynamic Base trick
    base_template = 'shared/base.html' if request.headers.get('HX-Request') else 'shared/base.html'

    context = {
        'staff': staff_member,
        'tasks': staff_tasks,
        'stats': stats,
        'base_template': base_template,
        'page_title': f"{staff_member.first_name}'s Profile"
    }
    
    return render(request, 'staffms/staff_profile.html', context)