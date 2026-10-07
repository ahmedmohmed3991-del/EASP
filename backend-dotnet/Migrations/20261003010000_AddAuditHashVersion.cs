using EASP.API.Data;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

namespace EASP.API.Migrations
{
    [DbContext(typeof(AppDbContext))]
    [Migration("20261003010000_AddAuditHashVersion")]
    public class AddAuditHashVersion : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Historical hashes remain untouched and continue through the legacy verifier.
            migrationBuilder.AddColumn<int>(name: "HashVersion", table: "AuditLogs", type: "int", nullable: false, defaultValue: 1);
        }
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Removing versions would silently reinterpret v2 hashes as legacy records.
            throw new InvalidOperationException("Audit hash version migration cannot be rolled back after v2 writes");
        }
    }
}
