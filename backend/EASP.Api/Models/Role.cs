using Microsoft.AspNetCore.Identity;

namespace EASP.Api.Models;

// IdentityRole (جاهز من .NET) بيدّيك Id + Name + NormalizedName.
// كلاس فاضي دلوقتي، بس عامله class مستقل عشان لو حبينا نضيف
// حقل زي "Description" للدور لاحقًا، نلاقيه جاهز.
public class Role : IdentityRole
{
}

// الأدوار الافتراضية اللي المشروع محتاجها (T-P01-010).
// عاملينها static class بسيطة عشان أي مكان في الكود يقدر يرجعلها
// من غير ما يكتب النص (string) يدوي كل مرة ويغلط في الإملاء.
public static class DefaultRoles
{
    public const string Employee = "Employee";
    public const string Analyst = "Analyst";
    public const string Administrator = "Administrator";

    public static readonly string[] All = { Employee, Analyst, Administrator };
}
