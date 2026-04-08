from django.db import models
from accounts.models import User
from bms import settings # Tumhara custom user model

# 1. TAGS / LABELS
class Tag(models.Model):
    company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=50, default='bg-blue-100 text-blue-800') # Tailwind classes
    
    def __str__(self):
        return self.name

class Task(models.Model):
    STATUS_CHOICES = (
        ('pending', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    # Basic Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Relations (Kaun bana raha hai, kisko de raha hai)
    company = models.ForeignKey('accounts.Company', on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    
    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.status}"
    



# --- TERA PURANA TASK MODEL YAHAN HAI ---
# class Task(models.Model):
#     ... (tera existing code) ...

# 2. SUBTASKS (Checklists)
class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.task.title} - {self.title}"

# 3. COMMENTS
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.first_name} on {self.task.title}"

# 4. ATTACHMENTS (Files & Screenshots)
class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
