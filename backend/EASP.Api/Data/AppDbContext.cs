using EASP.Api.Models;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace EASP.Api.Data;

// IdentityDbContext<User, Role, string> هو المكافئ لـ Mongoose schemas
// اللي كان مطلوب في التاسك الأصلي. الفرق إن ده بيجيب معاه تلقائيًا
// كل الجداول اللي Identity محتاجها (Users, Roles, UserRoles, UserClaims،
// إلخ) — مش لازم تعمل حاجة منهم يدوي.
public class AppDbContext : IdentityDbContext<User, Role, string>
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    // جداول Phase 4/5 (TokenMapping, Policy, AuditLog) هتتضاف هنا
    // كل ما نوصل لتاسكاتهم — دلوقتي بنركز على Phase 1 بس.

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder); // لازم تتنادى الأول عشان جداول Identity تتظبط صح

        // مثال: لو حبينا نضيف قيود إضافية على User لاحقًا، هنا مكانها.
        // builder.Entity<User>().Property(u => u.FullName).HasMaxLength(200);
    }
}
