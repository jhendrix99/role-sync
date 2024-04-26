import discord
from discord.ext import commands
import os
import time

# Manually load environment variables since the dotenv package isn't working
def load_env():
    env_file = ".env"
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

load_env()
parent_id = int(os.environ.get('PARENT_SERVER_ID'))
token = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Set some global variables
guild_data = {}
parent_roles = {}

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    game = discord.Game("Ready to !sync")
    await bot.change_presence(activity=game)

@bot.command()
async def sync(ctx):
    author = ctx.author
    allowed_roles = ["S1-Personnel", "S1-Adjutant", "Officer", "High Command", "Colonel"]

    # Check if the author has any of the allowed roles
    if any(role.name in allowed_roles for role in author.roles):
        game = discord.Game("Syncing Servers.")
        await bot.change_presence(activity=game)
        await ctx.send("Syncing, this will take a while. I will let you know when I'm done.")
        print(f"Sync command triggered by {author.name}#{author.discriminator}")
        await sync_guild_roles()
        await sync_member_roles()
        await ctx.send(f"{author.mention} Syncing has completed.")
        print("I have finished syncing all members and roles.")
    else:
        await ctx.send(f"{author.mention} You do not have permissions to run this command.")
        game = discord.Game("Ready to !sync")
        await bot.change_presence(activity=game)
    game = discord.Game("Ready to !sync")
    await bot.change_presence(activity=game)
    

async def sync_guild_roles():
    for guild in bot.guilds:
        time.sleep(0.35)
        if guild.id != parent_id:
            await sync_roles(guild)
    print("All guild roles synced.")

async def sync_roles(guild):
    global parent_roles
    parent_guild = bot.get_guild(parent_id)
    if parent_guild is None:
        print("Parent guild not found.")
        return

    parent_roles = {role.name: role.permissions for role in parent_guild.roles if role.name != "RoleSync"}

    for role_name, permissions in parent_roles.items():
        time.sleep(0.35)
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try:
                print(f"- Creating role: {role_name} with permissions {permissions}")
                role = await guild.create_role(name=role_name, permissions=permissions)
            except discord.errors.Forbidden as e:
                print(f"Error creating role: {e}")
                continue
        else:
            try:
                print(f"- Updating role: {role_name} with permissions {permissions}")
                await role.edit(permissions=permissions)
            except discord.errors.Forbidden as e:
                print(f"Error updating permissions for role {role_name}: {e}")
                continue

async def sync_member_roles():
    parent_guild = bot.get_guild(parent_id)
    if parent_guild is None:
        print("Parent guild not found.")
        return

    parent_member_data = {member.name: {"roles": [role.name for role in member.roles], "display_name": member.display_name} for member in parent_guild.members}
    
    for guild in bot.guilds:
        time.sleep(0.35)
        if guild.id != parent_id:
            await sync_members(guild, parent_member_data)

async def sync_members(guild, parent_member_data):
    for member_name, data in parent_member_data.items():
        time.sleep(0.35)
        member = discord.utils.get(guild.members, name=member_name)
        if member:
            try:
                # Collect roles to add
                roles_to_add = []
                for role_name in data["roles"]:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role and role not in member.roles:
                        roles_to_add.append(role)

                # Update member roles
                await member.add_roles(*roles_to_add)

                # Update member display name
                await member.edit(nick=data["display_name"])
                print(f"Synced member data for {member_name} in {guild.name}")
            except Exception as e:
                print(f"An error occurred while syncing member data for {member_name} in {guild.name}: {e}")
        else:
            print(f"Member {member_name} not found in {guild.name}")


bot.run(token)
