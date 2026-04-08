from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Task
from django.http import HttpResponse
from django.urls import reverse
from .forms import TaskForm

@login_required
def task_board(request):
    tasks = Task.objects.filter(company=request.user.company)
    
    # Context mein 3 alag lists bhej rahe hain
    context = {
        'pending_tasks': tasks.filter(status='pending'),
        'progress_tasks': tasks.filter(status='in_progress'),
        'completed_tasks': tasks.filter(status='completed'),
        'page_title': 'Task Board',
        # UI fix wala dynamic base
        'base_template': 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    }
    return render(request, 'taskms/board.html', context)

@login_required
def update_task_status(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id, company=request.user.company)
        new_status = request.POST.get('status')
        if new_status in ['pending', 'in_progress', 'completed']:
            task.status = new_status
            task.save()
        
        # Status update ke baad poora board refresh karne ke liye redirect
        return task_board(request)
    

@login_required
def add_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, company=request.user.company)
        if form.is_valid():
            task = form.save(commit=False)
            task.company = request.user.company
            task.created_by = request.user
            task.save()
            
            # Magic HTMX Trick: Task save hone ke baad modal band karo aur board refresh karo
            response = HttpResponse()
            response['HX-Trigger'] = 'boardRefresh'
            return response
    else:
        form = TaskForm(company=request.user.company)
        
    context = {'form': form, 'title': 'Create New Task', 'url': reverse('taskms:add_task')}
    return render(request, 'taskms/partials/task_modal.html', context)

# --- EDIT TASK ---
@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, company=request.user.company)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, company=request.user.company)
        if form.is_valid():
            form.save()
            response = HttpResponse()
            response['HX-Trigger'] = 'boardRefresh'
            return response
    else:
        form = TaskForm(instance=task, company=request.user.company)
        
    context = {'form': form, 'title': 'Edit Task', 'url': reverse('taskms:edit_task', args=[task.id])}
    return render(request, 'taskms/partials/task_modal.html', context)

# --- DELETE TASK ---
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, company=request.user.company)
    if request.method == 'POST':
        task.delete()
        response = HttpResponse()
        response['HX-Trigger'] = 'boardRefresh'
        return response