from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Folder, Document
from accounts.decorators import role_required

@login_required
def manager_home(request):
    company = request.user.company
    
    # RBAC: Agar private folder hai toh sirf Tier 1 ko dikhao
    folders = Folder.objects.filter(company=company)
    if not request.user.is_tier1:
        folders = folders.filter(is_private=False)
    
    # Saari files jo kisi folder mein nahi hain (Loose files)
    root_files = Document.objects.filter(company=company, folder__isnull=True)
    
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    return render(request, 'file_manager/dashboard.html', {
        'folders': folders,
        'root_files': root_files,
        'base_template': base_template,
        'page_title': 'File Storage'
    })

@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id, company=request.user.company)
    
    # Private folder check
    if folder.is_private and not request.user.is_tier1:
        return render(request, '403.html', status=403)
        
    files = folder.files.all()
    base_template = 'shared/base_partial.html' if request.headers.get('HX-Request') else 'shared/base.html'
    
    return render(request, 'file_manager/folder_detail.html', {
        'folder': folder,
        'files': files,
        'base_template': base_template
    })


from django.http import HttpResponse
from .forms import FolderForm, DocumentForm

@login_required
def create_folder(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.company = request.user.company
            folder.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'fileManagerRefresh'})
    else:
        form = FolderForm()
    return render(request, 'file_manager/partials/modal_folder.html', {'form': form})

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, company=request.user.company)
        
        if form.is_valid():
            doc = form.save(commit=False)
            doc.company = request.user.company
            doc.uploaded_by = request.user
            
            # Error Fix: Pehle check karo ki file actual mein upload hui hai ya nahi
            if 'file' in request.FILES:
                doc.file_size = request.FILES['file'].size
                
            doc.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'fileManagerRefresh'})
        else:
            # Agar form valid nahi hai (jaise title missing), toh wapas modal dikhao error ke sath
            return render(request, 'file_manager/partials/modal_upload.html', {'form': form})
            
    else:
        form = DocumentForm(company=request.user.company)
        
    return render(request, 'file_manager/partials/modal_upload.html', {'form': form})