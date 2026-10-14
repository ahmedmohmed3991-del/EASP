using Microsoft.EntityFrameworkCore;
using EASP.API.Models;
using BCrypt.Net;

namespace EASP.API.Data
{
    public static class SeedData
    {
        public static async Task SeedAsync(AppDbContext context)
        {
            // Ensure DB is created
            await context.Database.MigrateAsync();

            // Seed Users
            if (!await context.Users.AnyAsync())
            {
                var users = new List<User>
                {
                    new User
                    {
                        Username = "admin",
                        Email = "admin@easp.local",
                        PasswordHash = BCrypt.Net.BCrypt.HashPassword("Password123!", workFactor: 12),
                        Role = "Administrator",
                        IsActive = true,
                        CreatedAt = DateTime.UtcNow
                    },
                    new User
                    {
                        Username = "analyst",
                        Email = "analyst@easp.local",
                        PasswordHash = BCrypt.Net.BCrypt.HashPassword("Password123!", workFactor: 12),
                        Role = "Analyst",
                        IsActive = true,
                        CreatedAt = DateTime.UtcNow
                    },
                    new User
                    {
                        Username = "employee",
                        Email = "employee@easp.local",
                        PasswordHash = BCrypt.Net.BCrypt.HashPassword("Password123!", workFactor: 12),
                        Role = "Employee",
                        IsActive = true,
                        CreatedAt = DateTime.UtcNow
                    }
                };
                await context.Users.AddRangeAsync(users);
                await context.SaveChangesAsync();
                Console.WriteLine("[SeedData] ✅ Users seeded: admin, analyst, employee");
            }

            // Seed Policies
            if (!await context.Policies.AnyAsync())
            {
                var policies = new List<Policy>
                {
                    new Policy
                    {
                        Name = "LOW_RISK_ALLOW",
                        Description = "Allow all requests with low risk scores below 0.35",
                        TargetRole = "All",
                        MinRiskScore = 0.0,
                        MaxRiskScore = 0.34,
                        Action = "ALLOW",
                        RequireDlpRedaction = false,
                        Priority = 10,
                        IsActive = true
                    },
                    new Policy
                    {
                        Name = "MEDIUM_RISK_REDACT",
                        Description = "Redact and tokenize sensitive data for medium risk requests (0.35–0.59)",
                        TargetRole = "All",
                        MinRiskScore = 0.35,
                        MaxRiskScore = 0.59,
                        Action = "REDACT",
                        RequireDlpRedaction = true,
                        Priority = 20,
                        IsActive = true
                    },
                    new Policy
                    {
                        Name = "HIGH_RISK_ESCALATE",
                        Description = "Escalate for analyst review on high risk requests (0.60–0.79)",
                        TargetRole = "All",
                        MinRiskScore = 0.60,
                        MaxRiskScore = 0.79,
                        Action = "ESCALATE",
                        RequireDlpRedaction = true,
                        Priority = 30,
                        IsActive = true
                    },
                    new Policy
                    {
                        Name = "CRITICAL_RISK_BLOCK",
                        Description = "Block all requests with critical risk score >= 0.80",
                        TargetRole = "All",
                        MinRiskScore = 0.80,
                        MaxRiskScore = 1.0,
                        Action = "BLOCK",
                        RequireDlpRedaction = true,
                        Priority = 5,
                        IsActive = true
                    },
                    new Policy
                    {
                        Name = "DLP_CREDENTIAL_REDACT",
                        Description = "Always redact detected credentials regardless of risk score",
                        TargetRole = "All",
                        MinRiskScore = 0.0,
                        MaxRiskScore = 1.0,
                        Action = "REDACT",
                        RequireDlpRedaction = true,
                        Priority = 1,
                        IsActive = true
                    }
                };
                await context.Policies.AddRangeAsync(policies);
                await context.SaveChangesAsync();
                Console.WriteLine("[SeedData] ✅ Policies seeded: 5 default policies");
            }
        }
    }
}
