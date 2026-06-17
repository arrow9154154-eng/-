import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os  # 👈 ระบบดึงค่าความลับที่ซ่อนไว้

# 1. ตั้งค่าบอทและเปิดสิทธิ์การเข้าถึงข้อมูล (Intents)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. ระบบเมื่อบอทพร้อมทำงาน และทำการซิงค์ (Sync) คำสั่งเข้าระบบ Discord
@bot.event
async def on_ready():
    print(f"🤖 บอทออนไลน์แล้วในชื่อ: {bot.user.name}")
    try:
        # สั่งให้บอทส่งคำสั่งทั้งหมดขึ้นระบบ Discord
        synced = await bot.tree.sync()
        print(f"✨ ซิงค์ Slash Commands สำเร็จทั้งหมด {len(synced)} คำสั่ง!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการซิงค์คำสั่ง: {e}")

# ========================================================
# 3. พื้นที่คำสั่ง 3 หน่อ (Slash Commands)
# ========================================================

# หน่อที่ 1: คำสั่ง /say (สั่งบอทพิมพ์ข้อความแทน)
@bot.tree.command(name="say", description="🗣️ สั่งให้บอทพิมพ์ข้อความแทนเรา")
@app_commands.describe(message="ข้อความที่ต้องการให้บอทพิมพ์", channel="เลือกห้องที่ต้องการให้ส่ง (เว้นไว้หากต้องการส่งห้องปัจจุบัน)")
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้ครับ!", ephemeral=True)
        return
    
    target_channel = channel if channel else interaction.channel
    try:
        await target_channel.send(message)
        await interaction.response.send_message(f"✅ ส่งข้อความเรียบร้อย!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ บอทไม่มีสิทธิ์ส่งข้อความในห้องนั้นครับ!", ephemeral=True)

# หน่อที่ 2: คำสั่ง /nuke (ระเบิดล้างห้องแชท)
@bot.tree.command(name="nuke", description="💥 ล้างข้อความทั้งหมดในห้องนี้ (สร้างห้องใหม่ทดแทน)")
async def nuke(interaction: discord.Interaction):
    if interaction.user != interaction.guild.owner and not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ ใช้ได้เฉพาะแอดมินหรือเจ้าของเซิร์ฟเท่านั้นครับ!", ephemeral=True)
        return

    channel = interaction.channel
    position = channel.position
    category = channel.category
    await interaction.response.send_message("💣 กำลังเริ่มกระบวนการล้างห้อง...", ephemeral=True)

    try:
        new_channel = await channel.clone(reason="Nuke Channel")
        await new_channel.edit(position=position, category=category)
        await channel.delete(reason="Nuke Channel")
        
        await new_channel.send("💥 **ห้องนี้โดนระเบิดล้างข้อความเรียบร้อยแล้วโดยแอดมิน!**")
        await new_channel.send("https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-nuclear-gif-16168231")
    except Exception as e:
        await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)

# หน่อที่ 3: คำสั่ง /ban_time (แบนแบบตั้งเวลาปลดอัตโนมัติ)
@bot.tree.command(name="ban_time", description="🔨 แบนสมาชิกแบบกำหนดวันปลดแบนอัตโนมัติ")
@app_commands.describe(member="เลือกคนที่ต้องการแบน", days="จำนวนวันที่ต้องการแบน", reason="เหตุผลในการแบน")
async def ban_time(interaction: discord.Interaction, member: discord.Member, days: int, reason: str = "ไม่ได้ระบุเหตุผล"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์แบนสมาชิกครับ!", ephemeral=True)
        return

    if member == interaction.user or member == interaction.guild.owner:
        await interaction.response.send_message("❌ คุณไม่สามารถแบนไอดีนี้ได้ครับ!", ephemeral=True)
        return

    try:
        await member.ban(delete_message_days=1, reason=f"{reason} (แบนเป็นเวลา {days} วัน)")
        await interaction.response.send_message(f"✅ แบน {member.mention} เรียบร้อยเป็นเวลา {days} วัน ข้อหา: {reason}")
        
        # รอนับถอยหลังตามจำนวนวัน
        seconds = days * 24 * 60 * 60
        await asyncio.sleep(seconds)
        
        # ปลดแบนเมื่อครบกำหนด
        await interaction.guild.unban(discord.Object(id=member.id), reason="ครบกำหนดเวลาแบน")
        await interaction.channel.send(f"🔓 ปลดแบนให้คุณ {member.name} เรียบร้อยแล้ว (ครบกำหนด {days} วัน)")
    except discord.Forbidden:
        await interaction.response.send_message("❌ ยศของบอทต่ำกว่ายศของเขาครับ!", ephemeral=True)

# ========================================================
# 4. เปิดรันบอทโดยเรียกใช้ค่าความลับที่ตั้งไว้
# ========================================================
bot.run(os.getenv("DISCORD_TOKEN"))
