using EASP.API.Data;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;

namespace EASP.API.Migrations
{
    [DbContext(typeof(AppDbContext))]
    [Migration("20261003000000_AddRefreshTokenExpiry")]
    public class AddRefreshTokenExpiry : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Existing refresh tokens have no trustworthy expiry and require a new login.
            migrationBuilder.AddColumn<DateTime>(
                name: "RefreshTokenExpiresAt", table: "Users", type: "datetime2", nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(name: "RefreshTokenExpiresAt", table: "Users");
        }
    }
}
