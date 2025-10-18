from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db, Template, User
from routers.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import re

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    content: str
    keywords: List[str]
    tags: List[str]
    description: Optional[str] = None

class TemplateResponse(BaseModel):
    id: int
    name: str
    content: str
    keywords: List[str]
    tags: List[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

class TemplateApply(BaseModel):
    template_id: int
    keyword_values: dict  # 关键词对应的值

@router.post("/", response_model=TemplateResponse)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建模板"""
    # 验证模板内容中是否包含所有关键词
    for keyword in template.keywords:
        if f"{{{keyword}}}" not in template.content:
            raise HTTPException(
                status_code=400, 
                detail=f"模板内容中缺少关键词: {keyword}"
            )
    
    db_template = Template(
        user_id=current_user.id,
        name=template.name,
        content=template.content,
        keywords=json.dumps(template.keywords, ensure_ascii=False),
        tags=json.dumps(template.tags, ensure_ascii=False),
        description=template.description
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # 转换JSON字段
    db_template.keywords = json.loads(db_template.keywords)
    db_template.tags = json.loads(db_template.tags)
    
    return db_template

@router.get("/", response_model=List[TemplateResponse])
async def get_templates(
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的模板列表"""
    templates = db.query(Template).filter(Template.user_id == current_user.id).all()
    
    # 转换JSON字段并过滤标签
    result = []
    for template in templates:
        template.keywords = json.loads(template.keywords)
        template.tags = json.loads(template.tags)
        
        if tag and tag not in template.tags:
            continue
            
        result.append(template)
    
    return result

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 转换JSON字段
    template.keywords = json.loads(template.keywords)
    template.tags = json.loads(template.tags)
    
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if template_update.name is not None:
        template.name = template_update.name
    if template_update.content is not None:
        template.content = template_update.content
    if template_update.keywords is not None:
        template.keywords = json.dumps(template_update.keywords, ensure_ascii=False)
    if template_update.tags is not None:
        template.tags = json.dumps(template_update.tags, ensure_ascii=False)
    if template_update.description is not None:
        template.description = template_update.description
    
    template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(template)
    
    # 转换JSON字段
    template.keywords = json.loads(template.keywords)
    template.tags = json.loads(template.tags)
    
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除模板"""
    template = db.query(Template).filter(
        Template.id == template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    
    return {"message": "模板删除成功"}

@router.post("/apply")
async def apply_template(
    apply_data: TemplateApply,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """应用模板"""
    template = db.query(Template).filter(
        Template.id == apply_data.template_id,
        Template.user_id == current_user.id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 解析关键词
    keywords = json.loads(template.keywords)
    
    # 检查是否提供了所有必需的关键词值
    for keyword in keywords:
        if keyword not in apply_data.keyword_values:
            raise HTTPException(
                status_code=400,
                detail=f"缺少关键词值: {keyword}"
            )
    
    # 应用模板
    result_content = template.content
    for keyword, value in apply_data.keyword_values.items():
        result_content = result_content.replace(f"{{{keyword}}}", value)
    
    return {
        "content": result_content,
        "template_name": template.name
    }

@router.post("/extract-keywords")
async def extract_keywords_from_text(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """从文本中提取可能的关键词（人名等）"""
    # 简单的人名提取逻辑，可以根据需要改进
    # 这里使用正则表达式提取可能的人名
    
    # 提取中文人名模式（2-4个字符的中文名）
    name_pattern = r'[\u4e00-\u9fa5]{2,4}(?=的|说|道|想|看|听|走|来|去|在|是|有|没|不|也|都|就|又|还|只|才|已|将|被|让|使|令|叫|喊|问|答|回|告|知|见|遇|找|寻|追|跟|随|带|拉|推|抱|抓|握|拿|放|扔|丢|给|送|交|递|传|接|收|取|得|获|失|丢|失|败|胜|赢|输|死|活|生|杀|救|帮|助|护|守|保|防|攻|击|打|踢|咬|抓|撕|切|砍|刺|射|投|扔|掷|抛|飞|跳|跑|走|爬|游|骑|开|关|启|停|始|终|完|结|成|败|胜|负|赢|输|对|错|是|非|真|假|好|坏|美|丑|大|小|高|低|长|短|粗|细|厚|薄|重|轻|快|慢|早|晚|新|旧|多|少|全|空|满|缺|有|无|存|在|出|入|上|下|前|后|左|右|东|西|南|北|中|内|外|里|外|间|边|角|处|地|方|位|置|点|线|面|体|形|状|色|彩|声|音|味|香|臭|甜|苦|酸|辣|咸|淡|冷|热|温|凉|干|湿|软|硬|光|暗|明|亮|清|浊|净|脏|新|鲜|老|旧|年|轻|幼|小|少|青|中|老|古|今|现|代|时|刻|分|秒|瞬|间|久|长|短|暂|永|恒|常|变|化|动|静|稳|乱|序|治|理|管|控|制|限|束|缚|绑|系|连|接|合|并|分|离|散|聚|集|会|遇|见|面|识|知|懂|解|明|白|清|楚|糊|涂|乱|错|误|对|准|确|实|真|正|直|弯|曲|圆|方|尖|钝|利|害|险|危|安|全|稳|固|牢|松|紧|宽|窄|深|浅|远|近|高|低|上|下|前|后|左|右|中|央|心|核|边|缘|角|落|头|尾|始|终|起|止|开|关|启|闭|通|堵|塞|流|动|止|停|行|走|跑|飞|游|爬|跳|蹦|跃|舞|唱|说|话|言|语|词|句|文|字|书|读|写|画|描|绘|刻|印|记|录|存|储|藏|隐|显|露|现|出|入|进|退|返|回|归|来|去|往|向|朝|对|面|背|转|换|变|改|修|补|治|疗|愈|康|复|健|壮|强|弱|病|伤|痛|疼|酸|麻|痒|舒|适|爽|快|乐|喜|欢|爱|恨|怒|气|愤|怒|恼|烦|忧|愁|悲|伤|哭|泣|笑|乐|喜|惊|奇|怪|异|常|正|反|倒|逆|顺|从|依|靠|赖|托|委|派|遣|送|迎|接|待|客|主|人|民|众|群|体|个|单|独|孤|寂|静|闹|吵|响|声|音|调|律|节|拍|快|慢|高|低|大|小|强|弱|轻|重|粗|细|尖|厚|薄|深|浅|明|暗|亮|黑|白|红|橙|黄|绿|青|蓝|紫|灰|棕|粉|彩|色|光|影|像|形|状|样|式|型|类|种|品|质|量|数|额|价|值|钱|财|富|贫|穷|缺|乏|足|够|多|少|全|部|分|半|双|对|单|个|只|件|条|根|支|枝|片|块|团|堆|群|批|套|副|幅|张|页|本|册|卷|集|部|章|节|段|句|词|字|符|号|码|数|字|母|音|调|声|响|静|默|言|语|话|说|讲|谈|论|议|商|量|计|算|数|理|化|物|生|史|地|政|经|法|医|农|工|商|学|教|育|养|培|训|练|习|学|会|能|力|技|巧|方|法|式|样|型|类|种|品|牌|标|志|记|号|码|名|称|字|词|语|句|文|章|书|本|册|卷|集|部|篇|段|节|条|款|项|目|录|单|表|格|图|像|画|照|片|影|视|频|音|乐|歌|曲|调|律|节|拍|舞|蹈|戏|剧|电|影|视|节|目|程|序|软|件|硬|件|设|备|器|具|工|机|械|车|船|飞|机|火|车|汽|车|自|行|车|摩|托|车|电|动|车|公|交|车|出|租|车|货|车|卡|车|拖|车|挂|车|房|车|游|艇|帆|船|轮|船|潜|艇|飞|机|直|升|机|战|斗|机|客|机|货|机|运|输|机|教|练|机|侦|察|机|轰|炸|机|攻|击|机|预|警|机|加|油|机|救|援|机|消|防|车|救|护|车|警|车|军|车|坦|克|装|甲|车|导|弹|火|箭|卫|星|宇|宙|飞|船|空|间|站|月|球|车|探|测|器|机|器|人|智|能|设|备|电|脑|计|算|机|服|务|器|网|络|互|联|网|手|机|电|话|座|机|传|真|机|打|印|机|复|印|机|扫|描|仪|投|影|仪|显|示|器|监|视|器|摄|像|头|录|像|机|照|相|机|摄|影|机|录|音|机|播|放|器|音|响|喇|叭|耳|机|麦|克|风|话|筒|遥|控|器|键|盘|鼠|标|触|摸|屏|显|示|屏|液|晶|屏|等|离|子|屏|投|影|屏|白|板|黑|板|写|字|板|画|板|绘|图|板|制|图|板|设|计|板|工|作|台|办|公|桌|会|议|桌|餐|桌|茶|几|床|沙|发|椅|子|凳|子|柜|子|架|子|箱|子|盒|子|袋|子|包|裹|容|器|瓶|罐|杯|碗|盘|碟|勺|叉|刀|筷|子|餐|具|厨|具|锅|碗|瓢|盆|桶|缸|坛|罐|瓶|壶|杯|碗|盘|碟|勺|叉|刀|铲|锅|铲|漏|勺|蒸|笼|烤|箱|微|波|炉|电|饭|煲|豆|浆|机|榨|汁|机|搅|拌|机|料|理|机|咖|啡|机|茶|具|酒|具|餐|具|厨|具|清|洁|用|品|洗|涤|剂|消|毒|剂|杀|虫|剂|除|草|剂|肥|料|农|药|种|子|幼|苗|花|草|树|木|植|物|动|物|宠|物|家|禽|家|畜|野|生|动|物|昆|虫|鱼|类|鸟|类|哺|乳|动|物|爬|行|动|物|两|栖|动|物|无|脊|椎|动|物|微|生|物|细|菌|病|毒|真|菌|藻|类|原|生|动|物|食|物|食|品|粮|食|蔬|菜|水|果|肉|类|蛋|类|奶|制|品|豆|制|品|调|料|香|料|饮|料|酒|类|茶|叶|咖|啡|果|汁|汽|水|矿|泉|水|纯|净|水|自|来|水|井|水|河|水|湖|水|海|水|雨|水|雪|水|冰|水|热|水|温|水|冷|水|开|水|生|水|熟|水|淡|水|咸|水|甜|水|苦|水|酸|水|辣|水|香|水|臭|水|清|水|浊|水|净|水|脏|水|新|鲜|水|陈|旧|水|流|动|水|静|止|水|深|水|浅|水|宽|水|窄|水|大|水|小|水|多|水|少|水|全|水|空|水|满|水|缺|水|有|水|无|水|存|水|在|水|出|水|入|水|上|水|下|水|前|水|后|水|左|水|右|水|东|水|西|水|南|水|北|水|中|水|内|水|外|水|里|水|外|水|间|水|边|水|角|水|处|水|地|水|方|水|位|水|置|水|点|水|线|水|面|水|体|水|形|水|状|水|色|水|彩|水|声|水|音|水|味|水|香|水|臭|水|甜|水|苦|水|酸|水|辣|水|咸|水|淡|水|冷|水|热|水|温|水|凉|水|干|水|湿|水|软|水|硬|水|光|水|暗|水|明|水|亮|水|清|水|浊|水|净|水|脏|水|新|水|鲜|水|老|水|旧|水)'
    
    names = re.findall(name_pattern, text)
    
    # 去重并过滤常见词汇
    common_words = {'的', '了', '在', '是', '有', '和', '就', '都', '被', '从', '以', '为', '上', '要', '出', '一', '会', '可', '这', '那', '他', '她', '它', '我', '你', '们', '什', '么', '怎', '样', '哪', '里', '时', '候', '地', '方', '人', '个', '说', '话', '看', '见', '听', '到', '想', '起', '来', '去', '过', '着', '了', '吗', '呢', '吧', '啊', '呀', '哦', '嗯', '哼', '嘿', '嘻', '哈', '呵', '嘿', '咦', '哇', '哎', '唉', '哟', '喂', '喔', '噢', '嗨', '咳', '咯', '嗯', '唔', '嗷', '哼', '哦', '啊', '呀', '哎', '唉', '哟', '喂', '喔', '噢', '嗨', '咳', '咯', '嗯', '唔', '嗷'}
    
    unique_names = []
    for name in names:
        if name not in common_words and name not in unique_names and len(name) >= 2:
            unique_names.append(name)
    
    # 生成建议的关键词映射
    suggested_keywords = {}
    for i, name in enumerate(unique_names[:10]):  # 最多10个关键词
        suggested_keywords[f"man{i+1}"] = name
    
    return {
        "extracted_names": unique_names,
        "suggested_keywords": suggested_keywords,
        "keyword_count": len(unique_names)
    }