# EASP — Scaffold (CS1, Phase P0)

الفولدرز دي مكافئة لتاسك P0 في جدول CS1 ("Scaffold backend/, frontend/,
ai-services/, data/, docs/, tests/, docker/ folders")، بس backend/ مبني
كمشروع **ASP.NET Core Web API** بدل Node.js/Express.

## هتشغّله ازاي عندك

لازم يكون عندك .NET 8 SDK متثبت على جهازك (مش موجود في البيئة اللي بنيت
بيها الملف ده). بعد كده:

```bash
cd backend/EASP.Api
dotnet restore
dotnet run
```

هيفتحلك Swagger على `http://localhost:5000/swagger` بمجرد ما تضيف
Controllers فعلية.

## إيه اللي جاهز دلوقتي (P0)

- `backend/EASP.Api/` — مشروع Web API فاضي بس متظبط: `.csproj` فيه كل
  الـ NuGet packages اللي هتحتاجها (EF Core + SQL Server, Identity, JWT,
  Swagger)، و`Program.cs` فيه تعليقات موضحة مكان كل حاجة (auth، middleware،
  DlpClient، SecurityEngineService، TTL cleanup) — عشان توصل بيها فيز P1
  فصاعدًا بالترتيب.
- `frontend/`, `ai-services/`, `data/`, `docs/`, `tests/` — فولدرز فاضية
  بملف README شارح دور كل واحد.
- `docker/docker-compose.yml` — stub فيه backend + SQL Server + ai-services،
  زي ما مطلوب في P0 ("empty service stubs").

## الخطوة الجاية (P1)

جوه `backend/EASP.Api/Models/` اعمل `User.cs` و`Role.cs`، وجوه `Data/`
اعمل `AppDbContext.cs`، وابدأ Migration أول ما يبقى عندك الـ entities.
