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
}
