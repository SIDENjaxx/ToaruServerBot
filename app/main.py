import asyncio
import os
import sys
import requests
from datetime import datetime
import traceback
import aiohttp
import aiocache
import base64
import json
from discord.ext import commands
import discord
from collections import defaultdict
from googletrans import Translator, LANGUAGES
import dotenv
from server import server_thread




# Botの設定
bot = commands.Bot(command_prefix = ("!"), intents=discord.Intents.all())
translator = Translator()

dotenv.load_dotenv()
TOKEN = os.environ.get("TOKEN")

# 運営ロールをチェックするカスタムチェック関数
def is_admin(ctx):
    # もしメッセージを送信したメンバーが運営ロールを持っている場合はTrueを返します
    return any(role.name == 'staff' for role in ctx.author.roles)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)

    """bot起動"""
    channel = bot.get_channel(1235914351333085204)
    if channel:
        embed = discord.Embed(title="ボットが起動しました", color=discord.Color.green())
        await channel.send(embed=embed)
    else:
        print("準備完了")

    # ボットがオンラインの場合
    if bot.is_ready():
        await bot.change_presence(activity=discord.Game(name=f'とある。鯖'))
    # ボットがオフラインの場合
    else:
        await bot.change_presence(activity=None)

    await bot.tree.sync()


#bot.command


cache = aiocache.Cache()

@bot.hybrid_command(name="minecraft-skin")
async def skin(ctx, *, username):
    async with aiohttp.ClientSession() as session:
        try:
            # Check cache first
            uuid = await cache.get(username)
            if not uuid:
                # If not in cache, get UUID from Mojang API
                async with session.get(f'https://api.mojang.com/users/profiles/minecraft/{username}') as r:
                    if r.status == 200:
                        data = await r.json()
                        uuid = data['id']
                        # Store UUID in cache for 1 hour
                        await cache.set(username, uuid, ttl=60*60)

            # Get skin URL using UUID
            async with session.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}') as r:
                if r.status == 200:
                    data = await r.json()
                    properties = data['properties'][0]
                    decoded = base64.b64decode(properties['value']).decode('utf-8')
                    skin_url = json.loads(decoded)['textures']['SKIN']['url']

            # Send skin image
            embed = discord.Embed(title=f"{username}'s Minecraft Skin")
            embed.set_image(url=skin_url)
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"エラーが発生しました: {str(e)}")


@bot.hybrid_command(name="top")
async def top(ctx):
    """最上部のメッセージに飛ぶコマンド"""
    # メッセージのリストを取得し、最初のメッセージを取得します
    async for message in ctx.channel.history(limit=1, oldest_first=True):
        # メッセージが見つかった場合、Embedを作成して送信します
        if message:
            embed = discord.Embed(title="最上部のメッセージ", description=message.content, color=discord.Color.blue())
            embed.add_field(name="送信者", value=message.author.mention, inline=False)
            embed.add_field(name="リンク", value=f"[メッセージへのリンク]({message.jump_url})", inline=False)
            await ctx.send(embed=embed)
            break
    else:
        await ctx.send("メッセージが見つかりませんでした")


@bot.hybrid_command(name="translate")
async def translate(ctx, *, arg):
    """日本語に翻訳するコマンド"""
    translator = Translator(service_urls=['translate.google.com'])
    translation = translator.translate(arg, dest='ja')
    embed = discord.Embed(title="翻訳結果", color=0x00ff00)
    embed.add_field(name="翻訳言語", value=LANGUAGES[translation.src], inline=True)
    embed.add_field(name="翻訳前", value=translation.origin, inline=True)
    embed.add_field(name="翻訳語", value=translation.text, inline=True)
    await ctx.send(embed=embed)


def restart_bot():
    os.execv(sys.executable, ['python'] + sys.argv)

@bot.hybrid_command(name='restart')
@commands.guild_only()  # サーバー上でのみ実行可能にする
@commands.check(is_admin)
async def restart(ctx):
    """このbotを再起動するコマンド(運営のみ)"""
    embed = discord.Embed(
        title="再起動中",
        description="ボットを再起動しています...",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)
    restart_bot()

@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="エラー",
            description="このコマンドはボットの所有者のみが利用できます。",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@restart.error
async def restart_error(ctx, error):
    """エラー"""
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="エラー",
            description="このコマンドはボットの所有者のみが利用できます。",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.hybrid_command(name="botinfo", aliases=["ボット情報"])
async def botinfo(ctx):
    """このbotの情報を表示するコマンド"""
    bot_embed = discord.Embed(
        title="🤖 ボット情報",
        description="以下は、このボットの情報です。",
        color=0x3498db  # カスタマイズ可能な色
    )
    # ボットの情報を追加
    bot_embed.add_field(name="名前", value=bot.user.name, inline=True)
    bot_embed.add_field(name="ID", value=bot.user.id, inline=True)
    bot_embed.add_field(name="作成日時", value=bot.user.created_at.strftime("%Y-%m-%d %H:%M"), inline=True)
    bot_embed.add_field(name="ボットバージョン", value="1.0", inline=True)
    bot_embed.add_field(name="ボット開発者", value="<@993422862000062485>", inline=True)
    await ctx.send(embed=bot_embed)


@bot.hybrid_command(name="roleinfo")
@commands.check(is_admin)
async def roleinfo(ctx, *, role: discord.Role):
    """指定したロールの情報を表示するコマンド"""
    embed = discord.Embed(title=f'ロール情報: {role.name}', color=role.color)
    embed.add_field(name='ID', value=role.id, inline=True)
    embed.add_field(name='メンバー数', value=len(role.members), inline=True)
    embed.add_field(name='作成日時', value=f"<t:{int(role.created_at.timestamp())}:F>", inline=True)
    embed.add_field(name='カラーコード', value=role.color, inline=True)
    embed.add_field(name='役職が表示されるか', value=role.hoist, inline=True)
    embed.add_field(name='管理者権限', value=role.permissions.administrator, inline=True)
    embed.add_field(name='メンション可能か', value=role.mentionable, inline=True)

    await ctx.send(embed=embed)

@roleinfo.error
async def roleinfo_error(ctx, error):
    """ロール表示エラー"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("コマンドの使用法: `!roleinfo [ロール名]`")


@bot.hybrid_command()
async def serverinfo(ctx):
    """サーバーの情報を表示するコマンド"""
    server = ctx.guild
    server_id = server.id
    server_name = server.name
    server_created_at = server.created_at
    num_channels = len(server.channels)
    num_users = len(server.members)
    server_icon_url = str(server.icon.url) if server.icon else None

    embed = discord.Embed(title=f"{server.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=server_id, inline=True)
    embed.add_field(name="名前", value=server_name, inline=True)
    embed.add_field(name="サーバー作成日時", value=f"<t:{int(server.created_at.timestamp())}:F>", inline=True)
    embed.add_field(name="チャンネル数", value=num_channels, inline=True)
    embed.add_field(name="ユーザー数", value=num_users, inline=True)
    if server_icon_url:
        embed.set_thumbnail(url=server_icon_url)

    await ctx.send(embed=embed)

@bot.hybrid_command()
async def userinfo(ctx, member: discord.Member = None):
    """指定したユーザーの情報を表示するコマンド"""
    if member is None:
        member = ctx.message.author

    roles = [role.mention for role in member.roles if role.name != "@everyone"]

    joined_at = member.joined_at
    created_at = member.created_at

    embed = discord.Embed(title=f"{member.name}", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="グローバルネーム", value=member.display_name, inline=True)
    embed.add_field(name="アカウント作成日時", value=f"<t:{int(created_at.timestamp())}:F>", inline=True)
    embed.add_field(name="サーバー参加日時", value=f"<t:{int(joined_at.timestamp())}:F>", inline=True)
    embed.add_field(name="役職", value=", ".join(roles), inline=True)
    embed.add_field(name="ニックネーム", value=member.nick if member.nick else "なし", inline=True)
    embed.set_thumbnail(url=member.display_avatar)

    await ctx.send(embed=embed)


@bot.hybrid_command(name="weather")
async def advanced_weather(ctx, prefectures):
    """指定した都道府県の天気予報を表示するコマンド"""
    try:
        api_key = "9cd00891a519224dfe93779c47eb89ad"
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": prefectures, "appid": api_key, "units": "metric"}

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=10) as response:
                data = await response.json()

        if data["cod"] == "404":
            message = f'都市 "{prefectures}" が見つかりませんでした。'
        else:
            temperature = data["main"]["temp"]
            min_temperature = data["main"]["temp_min"]
            max_temperature = data["main"]["temp_max"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            detailed_weather = data["weather"][0]["description"]
            pressure = data["main"]["pressure"]
            visibility = data["visibility"]

            embed = discord.Embed(
                title=f"{prefectures}の現在の天気",
                description=f"詳細な天気: {detailed_weather}",
                color=0x3498db
            )
            embed.add_field(name="気温", value=f"{temperature}℃", inline=True)
            embed.add_field(name="最低気温", value=f"{min_temperature}℃", inline=True)
            embed.add_field(name="最高気温", value=f"{max_temperature}℃", inline=True)
            embed.add_field(name="湿度", value=f"{humidity}%", inline=True)
            embed.add_field(name="風速", value=f"{wind_speed} m/s", inline=True)
            embed.add_field(name="気圧", value=f"{pressure} hPa", inline=True)
            embed.add_field(name="視程", value=f"{visibility/1000} km", inline=True)

            message = None

        await ctx.send(content=message, embed=embed)
    except aiohttp.ClientConnectorError as e:
        await ctx.send(f'接続エラーが発生しました: {e}')
    except asyncio.TimeoutError as e:
        await ctx.send(f'タイムアウトエラーが発生しました: {e}')
    except Exception as e:
        await ctx.send(f'エラーが発生しました: {e}')


@bot.hybrid_command(name="purge")
@commands.check(is_admin)
async def clear(ctx, amount: int = 1, user: discord.Member = None, *, content: str = None):
    """メッセージを削除するコマンド(運営のみ)"""
    if amount < 1:
        await ctx.send("削除するメッセージ数は1以上でなければなりません。")
        return

    def check_message(message):
        if user and message.author != user:
            return False
        if content and content.lower() not in message.content.lower():
            return False
        return True

    deleted = []
    async for message in ctx.channel.history(limit=None):
        if len(deleted) >= amount:
            break
        if check_message(message):
            deleted.append(message)
            await message.delete()

    embed = discord.Embed(title="メッセージ削除完了", description=f"削除されたメッセージ数: {len(deleted)}", color=discord.Color.green())
    await ctx.send(embed=embed, delete_after=5)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("このコマンドを実行する権限がありません。管理者権限が必要です。")


existing_tickets = {}  # ユーザーごとの既存のチケットを格納する辞書
deleted_tickets = set()  # 削除されたチケットの内容を格納するセット


@bot.hybrid_command(name="ticket-add")
async def ticket(ctx, *, issue: str):
    """チケットを作成するコマンド"""
    user_id = ctx.author.id
    if issue in deleted_tickets:
        deleted_tickets.remove(issue)  # 削除されたチケットのセットから削除する

    category = discord.utils.get(ctx.guild.categories, name="Tickets")
    if category is None:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        }
        category = await ctx.guild.create_category(name="Tickets", overwrites=overwrites)

    ticket_channel_name = issue[:50]  # チケットの内容から最初の50文字をチャンネル名に使用
    existing_channel = discord.utils.get(ctx.guild.text_channels, name=ticket_channel_name)
    if existing_channel:
        await ctx.send("すでにチケットが作成されています。")
        return

    channel = await category.create_text_channel(name=ticket_channel_name)
    await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)

    embed = discord.Embed(title="新しいチケットが作成されました", description=f"問題: {issue}", color=discord.Color.green())
    embed.add_field(name="チケット作成者", value=ctx.author.mention, inline=True)
    embed.add_field(name="チケットチャンネル", value=channel.mention, inline=True)
    message = await channel.send(embed=embed)
    await ctx.send("チケットが正常に作成されました！")
    existing_tickets[user_id] = issue
    await message.add_reaction("🔒")



@ticket.error
async def ticket_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("チケットの内容を提供してください。例: `!ticket サーバーがダウンしています`")


@bot.hybrid_command(name="permissions")
async def permissions(ctx, channel: discord.TextChannel=None, *, member: discord.Member=None):
    """指定したチャンネルまたはユーザーの権限を表示するコマンド"""
    if not member:
        member = ctx.message.author
    if not channel:
        channel = ctx.channel

    # 権限とその説明を定義
    permissions = {
        'General': {
            'administrator': '全ての権限を持つ',
            'view_audit_log': '監査ログを見る',
            'manage_guild': 'サーバーを管理する',
            'manage_roles': 'ロールを管理する',
            'manage_channels': 'チャンネルを管理する',
            'kick_members': 'メンバーをキックする',
            'ban_members': 'メンバーをBANする',
            'create_instant_invite': '招待を作成する',
            'change_nickname': 'ニックネームを変更する',
            'manage_nicknames': 'ニックネームを管理する'
        },
        'Text': {
            'read_messages': 'メッセージを読む',
            'send_messages': 'メッセージを送信する',
            'send_tts_messages': 'TTSメッセージを送信する',
            'manage_messages': 'メッセージを管理する',
            'embed_links': 'リンクを埋め込む',
            'attach_files': 'ファイルを添付する',
            'read_message_history': 'メッセージの履歴を読む',
            'mention_everyone': '@everyone, @here, and all rolesをメンションする',
            'use_external_emojis': '外部の絵文字を使用する'
        },
        'Voice': {
            'connect': '接続する',
            'speak': '話す',
            'mute_members': 'メンバーをミュートする',
            'deafen_members': 'メンバーの音声を遮断する',
            'move_members': 'メンバーを移動する',
            'use_voice_activation': '音声検出を使用する'
        }
    }

    # 絵文字で権限の有無を表示
    enabled = '✅'
    disabled = '❌'

    embed = discord.Embed(title=f'{member} の {channel.name} チャンネルでの権限')
    for category, perms in permissions.items():
        value = '\n'.join(f'{enabled if getattr(channel.permissions_for(member), perm) else disabled} {perm}: {desc}' for perm, desc in perms.items())
        embed.add_field(name=category, value=value, inline=True)

    await ctx.send(embed=embed)






















#bot.event



@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return
    if payload.emoji.name == "🔒":
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author == bot.user:
            # 削除されたチケットの内容を記録
            issue = message.embeds[0].description.split(': ')[1]  # チケットの内容を取得
            deleted_tickets.add(issue)  # 削除されたチケットの内容をセットに追加
            await channel.delete()






@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return  # Botの場合は無視する

    if member.guild.id != 1188777445403398154:
        return  # 特定のサーバー以外は無視する

    channel_id = 1235915185634414664  # 通知を送信したいチャンネルのIDに置き換える
    notification_channel = bot.get_channel(channel_id)

    # ボイスチャンネル更新時の処理
    # ボットが接続している通話を取得
    voice_client = member.guild.voice_client

    if voice_client is not None:
        # 通話に他のメンバーがいなくなった場合
        if len(voice_client.channel.members) == 1:  # ボット自身も含まれているので1を引く
            # 通話から切断
            await voice_client.disconnect()

    """一時的なチャンネル作成"""
    if before.channel is None and after.channel and after.channel.id == 1235915372448841768:
        category = after.channel.category
        new_channel_name = f"{member.display_name}'s Channel"
        new_channel = await category.create_voice_channel(new_channel_name)
        await member.move_to(new_channel)
    elif before.channel and not after.channel:
        if before.channel.name == f"{member.display_name}'s Channel":
            # チャンネルがまだ存在するか確認
            existing_channel = discord.utils.get(member.guild.voice_channels, name=f"{member.display_name}'s Channel")
            if existing_channel:
                await existing_channel.delete()
    elif before.channel and after.channel and before.channel != after.channel:
        if before.channel.name == f"{member.display_name}'s Channel":
            # チャンネルがまだ存在するか確認
            existing_channel = discord.utils.get(member.guild.voice_channels, name=f"{member.display_name}'s Channel")
            if existing_channel:
                await existing_channel.delete()

    # ボイスチャンネル参加/切断時の通知処理
    if before.channel is None and after.channel is not None:
        # 通話に参加した場合
        channel_mention = after.channel.mention
        member_mentions = ' '.join([m.mention for m in after.channel.members if not m.bot])  # 参加しているBot以外のメンバーのメンションのリストを作成
        embed = discord.Embed(title="通話参加通知", description=f"{member.mention} さんが {channel_mention} に参加しました。\n現在のメンバー:\n{member_mentions}", color=discord.Color.green())
        await notification_channel.send(embed=embed)

    elif before.channel is not None and after.channel is None:
        # 通話から切断された場合
        channel_mention = before.channel.mention
        member_mentions = ' '.join([m.mention for m in before.channel.members if not m.bot])  # 参加しているBot以外のメンバーのメンションのリストを作成
        embed = discord.Embed(title="通話切断通知", description=f"{member.mention} さんが {channel_mention} から切断されました。\n現在のメンバー:\n{member_mentions}", color=discord.Color.red())
        await notification_channel.send(embed=embed)




spam_count = defaultdict(int)
spam_time = defaultdict(int)
spam_messages = defaultdict(list)
deleted_messages = set()

@bot.event
async def on_message_delete(message):
    global deleted_messages
    deleted_messages.add(message.id)

@bot.event
async def on_message(message):
    global spam_count
    global spam_time
    global spam_messages
    global deleted_messages

    # メッセージ送信者がbotの場合は無視
    if message.author.bot:
        return

    user_id = message.author.id
    now = message.created_at.timestamp()

    # 5秒以内の連投かどうかをチェック
    if now - spam_time[user_id] < 5:
        spam_count[user_id] += 1
        spam_messages[user_id].append(message)
        if spam_count[user_id] >= 5:
            # 5回以上連投したらメッセージを削除
            for msg in spam_messages[user_id]:
                if msg is not None and msg.id not in deleted_messages:
                    try:
                        await msg.delete()
                    except discord.NotFound:
                        pass
            # 通知用のembedを作成
            embed = discord.Embed(title="スパム行為の警告", description=f"{message.author.mention}さんがスパム行為を行いました。", color=0xff0000)
            # 連投したメッセージと時間とチャンネルとユーザーを表示
            for msg in spam_messages[user_id]:
                embed.add_field(name="メッセージ", value=f"```{msg.content}```", inline=False)
                embed.add_field(name="時間", value=msg.created_at.strftime("%Y/%m/%d %H:%M:%S"), inline=True)
                embed.add_field(name="チャンネル", value=msg.channel.mention, inline=True)
                embed.add_field(name="ユーザー", value=msg.author.mention, inline=True)
            # 通知チャンネルにembedを送信（通知チャンネルのIDを適切に設定してください）
            notify_channel = bot.get_channel(1235919103085121566)
            await notify_channel.send(embed=embed)
            # スパムカウントとメッセージをリセット
            spam_count[user_id] = 0
            spam_messages[user_id] = []
    else:
        spam_count[user_id] = 1
        spam_messages[user_id] = [message]

    spam_time[user_id] = now

    if message.guild and message.guild.id != 1188777445403398154:
        return

    if message.embeds:
        embed = message.embeds[0]
        trans_fields = []

        for field in embed.fields:
            trans_name = translator.translate(field.name, dest="ja").text
            trans_value = translator.translate(field.value, dest="ja").text
            trans_fields.append((trans_name, trans_value))

        trans_title = translator.translate(embed.title, dest="ja").text if embed.title else ""
        trans_desc = translator.translate(embed.description, dest="ja").text if embed.description else ""

        trans_embed = discord.Embed(title=trans_title, description=trans_desc, color=embed.color, url=embed.url)

        for name, value in trans_fields:
            trans_embed.add_field(name=name, value=value, inline=False)

        await message.channel.send(f"{message.content}", embed=trans_embed)

    for word in message.content.split():
        if word.startswith('https://discord.com/channels/') or word.startswith('https://discordapp.com/channels/'):
            parts = word.split('/')
            if len(parts) == 7:
                guild_id, channel_id, message_id = parts[4], parts[5], parts[6]
                try:
                    guild = bot.get_guild(int(guild_id))
                    channel = None
                    if guild:
                        channel = guild.get_channel(int(channel_id))
                    else:
                        channel = await bot.fetch_channel(int(channel_id))
                    fetched_message = await channel.fetch_message(int(message_id))
                    invite_link = await channel.create_invite(max_age=300)
                    message_content = fetched_message.content

                    embed = discord.Embed()
                    embed.add_field(name=" ", value=f"```{message_content}```", inline=True)
                    embed.add_field(name="🗨️メッセージ詳細", value=f"サーバー：{guild.name}\n チャンネル：{channel.name}\n メッセージ：{fetched_message.author.display_name}\n メッセージ作成時間：{fetched_message.created_at.strftime('%Y/%m/%d %H:%M:%S')}", inline=False)
                    embed.set_author(name=fetched_message.author.display_name, icon_url=fetched_message.author.display_avatar)
                    embed.set_footer(text=fetched_message.author.guild.name, icon_url=fetched_message.author.guild.icon)

                    if fetched_message.attachments:
                        embed.set_image(url=fetched_message.attachments[0].url)

                    await message.channel.send(embed=embed)
                except discord.NotFound:
                    await message.channel.send("メッセージが見つかりませんでした。")
                except discord.Forbidden:
                    await message.channel.send("権限がありません。")
                except Exception as e:
                    print(e)
                    await message.channel.send("エラーが発生しました。")

    await bot.process_commands(message)



bot_role_id = 1188784364440518698
user_role_id = 1235833678035161170

# サーバー参加時の処理
@bot.event
async def on_member_join(member):
    # メンバーが参加したサーバーの特定
    guild = member.guild
    # Botかユーザーかを判定
    if member.bot:
        # Bot用のロールを取得
        role = guild.get_role(bot_role_id)
    else:
        # ユーザー用のロールを取得
        role = guild.get_role(user_role_id)
    # ロールが存在するか確認
    if role is not None:
        # ロールをメンバーに付与
        await member.add_roles(role)
        print(f"{member.display_name}に{role.name}のロールを付与しました。")

@bot.event
async def on_command(ctx):
    """コマンド使用ログ"""
    guild_id_to_log = 1188777445403398154  # ログを送信したいサーバーのIDに置き換えてください
    guild = ctx.guild  # コマンドが実行されたサーバーを取得

    # コマンドが実行されたサーバーのIDがログを送信したいサーバーのIDと一致するか確認
    if guild and guild.id == guild_id_to_log:
        channel = ctx.channel  # 使用されたチャンネルを取得

        embed = discord.Embed(title="コマンド使用ログ", color=0x00ff00)
        embed.add_field(name="使用コマンド", value=f"```{ctx.command}```", inline=False)
        command_time = ctx.message.created_at.strftime('%Y /%m / %d %H:%M')
        embed.add_field(name="使用時刻", value=command_time, inline=False)
        embed.add_field(name="チャンネル", value=channel.mention, inline=False)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)

        # 送信したいチャンネルのIDに置き換えてください
        channel_id = 1235912178746523759
        log_channel = bot.get_channel(channel_id)
        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print("指定したIDのチャンネルが見つかりません")


@bot.event
async def on_message_delete(message):
    """削除ログ"""
    if message.author.bot or message.guild.id != 1188777445403398154:  # あなたのサーバーのIDに置き換えてください
        return  # ボットのメッセージと他のサーバーからのメッセージは無視する

    log_channel_id = 1235912178746523759  # ログを送信するチャンネルのIDに置き換えてください
    log_channel = bot.get_channel(log_channel_id)

    if log_channel:
        now = datetime.now()  # 現在の日時を取得
        formatted_time = now.strftime('%Y /%m /%d %H:%M')  # 時刻をフォーマット
        embed = discord.Embed(title="メッセージ削除ログ", color=discord.Color.red())
        embed.add_field(name="メッセージ", value=f"```{message.content}```", inline=False)
        embed.add_field(name="時刻", value=formatted_time, inline=False)
        embed.add_field(name="チャンネル", value=message.channel.mention, inline=False)
        embed.set_footer(text=message.author.display_name, icon_url=message.author.display_avatar)

        # メッセージに画像が含まれている場合
        if message.attachments:
            image_urls = [attachment.url for attachment in message.attachments if attachment.width and attachment.height]
            if image_urls:
                for image_url in image_urls:
                    embed_with_image = embed.copy()
                    embed_with_image.set_image(url=image_url)
                    await log_channel.send(embed=embed_with_image)
        else:
            await log_channel.send(embed=embed)



@bot.event
async def on_message_edit(before, after):
    """メッセージ編集ログ"""
    if before.content != after.content and after.guild.id == 1188777445403398154:
        channel_id = 1235912178746523759  # ログを送信するチャンネルのID
        log_channel = bot.get_channel(channel_id)

        if log_channel:
            embed = discord.Embed(
                title="メッセージ編集ログ",
                color=discord.Color.blue()
            )
            embed.add_field(name="変更前", value=f"```{before.content}```", inline=False)  # 変更前のメッセージをコードブロックで表示
            embed.add_field(name="変更後", value=f"```{after.content}```", inline=False)   # 変更後のメッセージをコードブロックで表示
            if after.edited_at is not None:  # メッセージが編集された場合のみ時刻を表示
                embed.add_field(name="時刻", value=f"{after.edited_at.strftime('%Y /%m / %d %H:%M')}")
            embed.add_field(name="チャンネル", value=f"{after.channel.mention}", inline=False)
            embed.set_footer(text=after.author.display_name, icon_url=after.author.display_avatar)

            await log_channel.send(embed=embed)








# エラーログを出力するチャンネルのID
ERROR_LOG_CHANNEL_ID = 1235914351333085204

# エラーログを送信する関数
async def send_error_log(channel_id, event_name, error_message, ctx=None):
    error_log_channel = bot.get_channel(channel_id)
    if error_log_channel:
        embed = discord.Embed(title=f"An error occurred in event '{event_name}'", description="詳細情報は以下の通りです：", color=discord.Color.red())
        embed.add_field(name="エラーメッセージ", value=f"```{error_message}```", inline=True)
        if ctx:
            embed.add_field(name="発生したコンテキスト", value=f"サーバー: {ctx.guild.name} ({ctx.guild.id})\nチャンネル: {ctx.channel.name} ({ctx.channel.id})\nユーザー: {ctx.author.name} ({ctx.author.id})")
        embed.set_footer(text="エラーログが役立つ情報を提供するよう心がけてください。")
        await error_log_channel.send(embed=embed)
    else:
        print("エラーログのチャンネルが見つかりません。ERROR_LOG_CHANNEL_IDを確認してください。")

# エラーハンドラデコレータ
@bot.event
async def on_error(event, *args, **kwargs):
    """エラー"""
    error_message = traceback.format_exc()
    await send_error_log(ERROR_LOG_CHANNEL_ID, event, error_message)

# コマンドエラーハンドラデコレータ
@bot.event
async def on_command_error(ctx, error):
    """コマンドエラー"""
    if isinstance(error, commands.CommandError):
        error_message = getattr(error, 'original', error)
        await send_error_log(ERROR_LOG_CHANNEL_ID, f"コマンド '{ctx.command}'", str(error_message))




server_thread()
bot.run(TOKEN)  # Discord Developer Portalから取得したBotのトークンを入力
