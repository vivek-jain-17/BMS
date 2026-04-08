# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm, CompanyForm

@login_required
def profile_view(request):
    # Pass the current logged-in user as the instance
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'form': form,
        'page_title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def company_setup(request):
    # If they already have a company, kick them back to the dashboard
    if request.user.company:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            # Save the new company to the database
            new_company = form.save()
            
            # Link the logged-in user to this new company!
            request.user.company = new_company
            request.user.save()
            
            messages.success(request, f"Workspace for {new_company.name} created successfully!")
            return redirect('dashboard:home')
    else:
        form = CompanyForm()

    # We don't want the sidebar showing here, so we will use a dedicated standalone layout
    return render(request, 'accounts/company_setup.html', {'form': form})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_home(request):
    # THE GATEKEEPER: If user has no company, force them to the setup page
    if not request.user.company:
        return redirect('accounts:company_setup')

    context = {
        'page_title': 'Dashboard Overview'
    }
    return render(request, 'dashboard/index.html', context)