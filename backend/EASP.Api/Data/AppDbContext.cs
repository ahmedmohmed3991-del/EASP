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

    // Phase 4 & Phase 5 DbSets (TokenMapping, Policy, AuditLog)
    public DbSet<TokenMapping> TokenMappings => Set<TokenMapping>();
    public DbSet<Policy> Policies => Set<Policy>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder); // Identity table configuration

        builder.Entity<TokenMapping>(entity =>
        {
            entity.HasIndex(e => e.Token).IsUnique();
            entity.HasIndex(e => e.ExpiresAt);
        });

        builder.Entity<Policy>(entity =>
        {
            entity.HasIndex(e => e.Name);
            entity.HasIndex(e => e.Category);
        });

        builder.Entity<AuditLog>(entity =>
        {
            entity.HasIndex(e => e.Timestamp);
            entity.HasIndex(e => e.Action);
            entity.HasIndex(e => e.UserId);
        });
    }
}
