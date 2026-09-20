using EASP.Api.Models;
using Microsoft.AspNetCore.Identity;

namespace EASP.Api.Data;

// "Seed data" = بيانات ابتدائية بتتحط في قاعدة البيانات أول مرة تشتغل.
// هنا بننشئ الـ 3 أدوار الافتراضية (Employee, Analyst, Administrator)
// لو مش موجودين أصلاً — بتتنفذ مرة واحدة بس أول ما السيرفر يشتغل.
public static class DbSeeder
{
    public static async Task SeedRolesAsync(RoleManager<Role> roleManager)
    {
        foreach (var roleName in DefaultRoles.All)
        {
            var exists = await roleManager.RoleExistsAsync(roleName);
            if (!exists)
            {
                await roleManager.CreateAsync(new Role { Name = roleName });
            }
        }
    }

    public static async Task SeedDefaultPoliciesAsync(AppDbContext db)
    {
        var defaultPolicies = new List<Policy>
        {
            new Policy
            {
                Name = "Enterprise Prompt Injection Defense",
                Description = "Automatically block malicious prompt injections exceeding confidence threshold",
                Category = "PROMPT_INJECTION",
                Action = "Block",
                Severity = "High",
                IsEnabled = true,
                ConfigurationJson = "{\"threshold\": 80.0}"
            },
            new Policy
            {
                Name = "High Composite Risk Block",
                Description = "Enforce hard block when multi-modal composite risk score exceeds 70%",
                Category = "RISK",
                Action = "Block",
                Severity = "Critical",
                IsEnabled = true,
                ConfigurationJson = "{\"threshold\": 70.0}"
            },
            new Policy
            {
                Name = "Customer PII Redaction Policy",
                Description = "Automatically redact sensitive customer PII before sending prompts downstream",
                Category = "DLP",
                Action = "Redact",
                Severity = "Medium",
                IsEnabled = true,
                ConfigurationJson = "{\"entities\":[\"EMAIL_ADDRESS\",\"PHONE_NUMBER\",\"SSN\"]}"
            }
        };

        foreach (var policy in defaultPolicies)
        {
            if (!await Microsoft.EntityFrameworkCore.EntityFrameworkQueryableExtensions.AnyAsync(db.Policies, p => p.Name == policy.Name))
            {
                await db.Policies.AddAsync(policy);
            }
        }

        await db.SaveChangesAsync();
    }
}
