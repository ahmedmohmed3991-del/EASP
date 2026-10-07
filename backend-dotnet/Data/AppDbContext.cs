using Microsoft.EntityFrameworkCore;
using EASP.API.Models;

namespace EASP.API.Data
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

        public DbSet<User> Users { get; set; }
        public DbSet<AuditLog> AuditLogs { get; set; }
        public DbSet<Incident> Incidents { get; set; }
        public DbSet<Policy> Policies { get; set; }
        public DbSet<TokenMapping> TokenMappings { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Users
            modelBuilder.Entity<User>(e =>
            {
                e.HasIndex(u => u.Email).IsUnique();
                e.HasIndex(u => u.Username).IsUnique();
                e.Property(u => u.Role).HasDefaultValue("Employee");
            });

            // AuditLogs — append-only, no updates
            modelBuilder.Entity<AuditLog>(e =>
            {
                e.HasIndex(a => a.Timestamp);
                e.HasIndex(a => a.EventType);
                e.Property(a => a.Details).HasDefaultValue("{}");
            });

            // Incidents
            modelBuilder.Entity<Incident>(e =>
            {
                e.HasIndex(i => i.Status);
                e.HasIndex(i => i.CreatedAt);
                e.HasIndex(i => i.Severity);
            });

            // Policies
            modelBuilder.Entity<Policy>(e =>
            {
                e.HasIndex(p => p.Name).IsUnique();
                e.HasIndex(p => p.Priority);
            });

            // TokenMappings
            modelBuilder.Entity<TokenMapping>(e =>
            {
                e.HasIndex(t => t.TokenId).IsUnique();
                e.HasIndex(t => t.ExpiresAt);
            });
        }
    }
}
