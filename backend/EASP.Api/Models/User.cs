using Microsoft.AspNetCore.Identity;

namespace EASP.Api.Models;

// IdentityUser (جاهز من .NET) بيدّيك بالفعل: Id, UserName, Email, PasswordHash,
// PhoneNumber, وكل منطق تشفير الباسورد جاهز. إحنا بس بنضيف حقل واحد إضافي
// (FullName) اللي المشروع بتاعنا محتاجه ومش موجود في الأساس.
public class User : IdentityUser
{
    public string FullName { get; set; } = string.Empty;

    // تاريخ إنشاء الحساب — مفيد للـ Audit Log لاحقًا (Phase 5)
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
