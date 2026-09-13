import re
import io

with open('cogs/ticket/ticket.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Chunk 1: init_database
old = '''        conn.commit()

    async def cog_load(self):'''
new = '''        try:
            cursor.execute("ALTER TABLE ticket_config ADD COLUMN transcript_channel_id TEXT")
        except:
            pass

        conn.commit()

    async def cog_load(self):'''
code = code.replace(old, new)

# Chunk 2: get_config
old = '''        cursor.execute("SELECT category_id, support_role_id, log_channel_id, panel_channel_id, panel_message_id, ticket_counter FROM ticket_config WHERE guild_id = ?", (str(guild_id),))'''
new = '''        cursor.execute("SELECT category_id, support_role_id, log_channel_id, panel_channel_id, panel_message_id, ticket_counter, transcript_channel_id FROM ticket_config WHERE guild_id = ?", (str(guild_id),))'''
code = code.replace(old, new)

old = '''            "panel_message_id": int(row[4]) if row[4] else None,
            "ticket_counter": row[5] or 0
        }'''
new = '''            "panel_message_id": int(row[4]) if row[4] else None,
            "ticket_counter": row[5] or 0,
            "transcript_channel_id": int(row[6]) if len(row) > 6 and row[6] else None
        }'''
code = code.replace(old, new)

# Chunk 3: update_config
old = '''                "panel_channel_id": None, "panel_message_id": None, "ticket_counter": 0
            }'''
new = '''                "panel_channel_id": None, "panel_message_id": None, "ticket_counter": 0,
                "transcript_channel_id": None
            }'''
code = code.replace(old, new)

old = '''        cursor.execute("""
            UPDATE ticket_config
            SET category_id = ?, support_role_id = ?, log_channel_id = ?, panel_channel_id = ?, panel_message_id = ?, ticket_counter = ?
            WHERE guild_id = ?
        """, (
            str(current["category_id"]) if current["category_id"] else None,
            ",".join(str(x) for x in current["support_role_ids"]) if current.get("support_role_ids") else None,
            str(current["log_channel_id"]) if current["log_channel_id"] else None,
            str(current["panel_channel_id"]) if current["panel_channel_id"] else None,
            str(current["panel_message_id"]) if current["panel_message_id"] else None,
            current["ticket_counter"],
            str(guild_id)
        ))'''
new = '''        cursor.execute("""
            UPDATE ticket_config
            SET category_id = ?, support_role_id = ?, log_channel_id = ?, panel_channel_id = ?, panel_message_id = ?, ticket_counter = ?, transcript_channel_id = ?
            WHERE guild_id = ?
        """, (
            str(current["category_id"]) if current.get("category_id") else None,
            ",".join(str(x) for x in current["support_role_ids"]) if current.get("support_role_ids") else None,
            str(current["log_channel_id"]) if current.get("log_channel_id") else None,
            str(current["panel_channel_id"]) if current.get("panel_channel_id") else None,
            str(current["panel_message_id"]) if current.get("panel_message_id") else None,
            current.get("ticket_counter", 0),
            str(current["transcript_channel_id"]) if current.get("transcript_channel_id") else None,
            str(guild_id)
        ))'''
code = code.replace(old, new)

# Chunk 4: Helper Function generate_transcript_file
old = '''        return False

    # ─────────────────────────────────────────────────────────────'''
new = '''        return False

    async def generate_transcript_file(self, channel):
        transcript_text = f"=== 🎫 TICKET TRANSCRIPT : #{channel.name} ===\\n"
        transcript_text += f"Server: {channel.guild.name} ({channel.guild.id})\\n"
        from datetime import datetime, timezone
        transcript_text += f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\\n"
        transcript_text += "=" * 55 + "\\n\\n"
        
        messages = [msg async for msg in channel.history(limit=500, oldest_first=True)]
        for msg in messages:
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author_tag = f"{msg.author.name} ({msg.author.id})"
            transcript_text += f"[{ts}] {author_tag}: {msg.content}\\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_text += f"    [Attachment: {att.url}]\\n"
                    
        import io
        import discord
        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        return discord.File(file_bytes, filename=f"transcript-{channel.name}.txt")

    async def _send_auto_transcript(self, guild, channel, user_id):
        import discord
        from datetime import datetime, timezone
        cfg = self.get_config(guild.id)
        if cfg and cfg.get("transcript_channel_id"):
            t_chan = guild.get_channel(cfg["transcript_channel_id"])
            if t_chan:
                try:
                    file = await self.generate_transcript_file(channel)
                    embed = discord.Embed(
                        title="📜 Ticket Transcript Log",
                        description=f"Ticket **#{channel.name}** has been deleted.\\n**Creator ID:** <@{user_id}>",
                        color=discord.Color.dark_grey(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    await t_chan.send(embed=embed, file=file)
                except Exception as e:
                    print(f"Failed to send auto transcript: {e}")

    # ─────────────────────────────────────────────────────────────'''
code = code.replace(old, new, 1)

# Chunk 5: auto sending on deletion logic 1
old = '''        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket deleted by {user.name}")
        except Exception:
            pass'''
new = '''        await self._send_auto_transcript(guild, channel, row[0])
        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket deleted by {user.name}")
        except Exception:
            pass'''
code = code.replace(old, new)

# Chunk 6: auto sending on deletion logic 2
old = '''        await asyncio.sleep(5)
        try:
            await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author.name}")
        except Exception:
            pass'''
new = '''        await self._send_auto_transcript(ctx.guild, ctx.channel, row[0])
        await asyncio.sleep(5)
        try:
            await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author.name}")
        except Exception:
            pass'''
code = code.replace(old, new)

# Chunk 7: set-transcript command
new_cmd = '''
    @ticket.command(name="set-transcript")
    @commands.has_permissions(manage_guild=True)
    async def set_transcript(self, ctx, channel: discord.TextChannel):
        """Ticket transcript logs ke liye channel set karein (jab ticket delete ho toh yaha save hoga)."""
        self.update_config(ctx.guild.id, transcript_channel_id=channel.id)
        embed = discord.Embed(
            title="✅ Transcript Channel Configured",
            description=f"Ticket delete hone par transcript ab {channel.mention} me aayenge.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
'''
code = code.replace('''    @ticket.command(name="logs")''', new_cmd + '''\n    @ticket.command(name="logs")''')

# Apply transcript_ticket_logic using helper
old = '''        transcript_text = f"=== 🎫 TICKET TRANSCRIPT : #{channel.name} ===\\n"
        transcript_text += f"Server: {guild.name} ({guild.id})\\n"
        transcript_text += f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\\n"
        transcript_text += "=" * 55 + "\\n\\n"

        messages = [msg async for msg in channel.history(limit=500, oldest_first=True)]
        for msg in messages:
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author_tag = f"{msg.author.name} ({msg.author.id})"
            transcript_text += f"[{ts}] {author_tag}: {msg.content}\\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_text += f"    [Attachment: {att.url}]\\n"

        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        file = discord.File(file_bytes, filename=f"transcript-{channel.name}.txt")'''
new = '''        file = await self.generate_transcript_file(channel)'''
code = code.replace(old, new)

# For transcript command:
old = '''        transcript_text = f"=== 🎫 TICKET TRANSCRIPT : #{ctx.channel.name} ===\\n"
        transcript_text += f"Server: {ctx.guild.name} ({ctx.guild.id})\\n"
        transcript_text += f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\\n"
        transcript_text += "=" * 55 + "\\n\\n"

        messages = [msg async for msg in ctx.channel.history(limit=500, oldest_first=True)]
        for msg in messages:
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author_tag = f"{msg.author.name} ({msg.author.id})"
            transcript_text += f"[{ts}] {author_tag}: {msg.content}\\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_text += f"    [Attachment: {att.url}]\\n"

        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        file = discord.File(file_bytes, filename=f"transcript-{ctx.channel.name}.txt")'''
new = '''        file = await self.generate_transcript_file(ctx.channel)'''
code = code.replace(old, new)


with open('cogs/ticket/ticket.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Replaced Successfully")
