# cogs/fun_roast.py
import discord
from discord.ext import commands
import random

class FunRoast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.roasts = [
            "Bhai, teri shakal dekh kar lagta hai ki jab bhagwan dimaag baant rahe the, tab tu SRM ke bhandare me khana kha raha tha!",
            "Shauk toh bade bade hain par halat aisi hai ki market me 'Vim Bar' bhi EMI par lena pad jaye.",
            "Tujhse zyada dhyan toh log YouTube ke ads par deh rahe hain aaj kal.",
            "Tera dimaag ekdum naya hai, bilkul brand new... Kyunki tumne use kabhi khol kar use hi nahi kiya!",
            "Bhai tere se acche expressions toh thermal engineering ki boring classes me aa jaate hain.",
            "Tu itna bada loser hai ki agar koi 'Failure Competition' ho, toh tu usme bhi 2nd aayega!",
            "Bhai, teri baatein sun kar dimaag ke cells suicide kar lete hain.",
            "Teri shakal par sirf tera baap hi has sakta hai, wo bhi afsos ke sath.",
            "Agar dimaag bechne niklega na, toh 'Unused Condition' bol kar sabse zyada rate tera hi lagega.",
            "Tu wo naseebwala insaan hai jise dekh kar bhoot bhi apna rasta badal leta hai.",
            "Bhai, thoda dimaag coding me laga leta toh aaj bot chalane ki jagah khud koi dhasu startup chala raha hota.",
            "Teri har baat sunkar aisa lagta hai jaise kisi ne dimaag par slow-mode laga diya ho.",
            "Tu jahan khada hota hai na, wahan ki hawa bhi apna direction badal leti hai.",
            "Tera dimaag aur tera bank balance, dono ek doosre ko competition de rahe hain ki kaun pehle zero hoga.",
            "Bhai, teri personality dekh kar lagta hai ki tujhe 'Error 404' ne janam diya hai.",
            "Tere jaisa dimaag agar scientist ke paas hota, toh aaj hum chand ki jagah kachre ke dher par baithe hote.",
            "Tujhe dekh kar lagta hai ki bhagwan ne tujhe bina kisi blueprint ke hi tayaar kar diya.",
            "Teri dosti aur teri coding, dono par koi ek minute se zyada bharosa nahi kar sakta.",
            "Tu wo legend hai jo online class me bhi peeche ki seat dhoodhta hai.",
            "Bhai, teri baaton me itna darr hai jaise semester exam ke ek raat pehle ka syllabus.",
            "Tu dosto ke beech utna hi useful hai jitna bada laptop me internet explorer hota hai.",
            "Teri shakal par kisi ne 'Ctrl+Z' dabane ki koshish ki thi par lagta hai command beech me hi crash ho gaya.",
            "Bhai, tujhse zyada speed toh college ke low-end Wi-Fi me hoti hai.",
            "Tera dimaag dekh kar lagta hai ki usme hamesha buffering hi chalti rehti hai.",
            "Tu jahan jaata hai, wahan ka josh automatic dnd (do not disturb) status par chala jaata hai.",
            "Bhai, tujhe dimaag ki jagah bhagwan ne galti se kachra-box assign kar diya tha.",
            "Tu itna bada khiladi hai ki ludo me bhi tera token pehle ghar se nikalne se mana kar deta hai.",
            "Teri har baat sunkar lagta hai jaise koi purana system bina graphics card ke heavy game chala raha ho.",
            "Bhai, tere se bade roasts toh dosto ke group chat me bina bot ke hi thuk jaate hain.",
            "Tu wo insaan hai jo calculator me bhi 2+2 check karne ke liye do baar sochta hai.",
            "Bhai teri life ka scale ekdum khali database jaisa hai, jisme koi table hi nahi mili.",
            "Tujhe dekh kar lagta hai ki nature ne tere upar apna poora experiment fail kar diya.",
            "Bhai, tere bolne se pehle tera dimaag hamesha 'Not Responding' dikha deta hai.",
            "Tu server me utna hi akela hai jitna engineering me ladkiyaan hoti hain.",
            "Bhai, tujhse bade logic toh bot ke crash errors me mil jaate hain.",
            "Tera dimaag ekdum cloud jaisa hai... Hamesha khali aur hawa me udta rehta hai!"
        ]

    @commands.command(name="roast")
    async def roast(self, ctx, member: discord.Member = None):
        """Kisi ki dosto ke beech witty Hinglish roasts ke sath taang kheenchte hain."""
        member = member or ctx.author
        roast_text = random.choice(self.roasts)
        await ctx.send(f"🔥 {member.mention}, {roast_text}")

async def setup(bot):
    await bot.add_cog(FunRoast(bot))