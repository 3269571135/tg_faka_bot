import threading
import telegram
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN, ADMIN_ID, ADMIN_COMMAND_START, ADMIN_COMMAND_QUIT, PAY_TIMEOUT
import sqlite3
import time
import datetime
import random
import os
from epay import make_data_dict, epay_submit, check_status

ROUTE, CATEGORY, PRICE, SUBMIT, TRADE = range(5)
ADMIN_ROUTE, ADMIN_CATEGORY_ROUTE, CATEGORY_FUNC_EXEC, ADMIN_GOODS_ROUTE, ADMIN_GOODS_STEP1, ADMIN_GOODS_STEP2, \
ADMIN_CARD_ROUTE, ADMIN_TRADE_ROUTE, ADMIN_CARD_STEP1, ADMIN_CARD_STEP2, ADMIN_TRADE_EXEC = range(11)
bot = telegram.Bot(token=TOKEN)


def run_bot():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    admin_handler = ConversationHandler(
        entry_points=[CommandHandler(ADMIN_COMMAND_START, admin)],

        states={
            ADMIN_ROUTE: [
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('分类') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('商品') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('卡密') + '$'),
                CallbackQueryHandler(admin_entry_route, pattern='^' + str('订单') + '$'),
            ],
            ADMIN_CATEGORY_ROUTE: [
                CallbackQueryHandler(category_func_route, pattern='^' + '(添加|删除)分类' + '$'),
            ],
            CATEGORY_FUNC_EXEC: [
                CommandHandler('{}'.format(ADMIN_COMMAND_QUIT), icancel),
                MessageHandler(Filters.text, category_func_exec),
                CallbackQueryHandler(category_func_exec, pattern='.*?')
            ],
            ADMIN_GOODS_ROUTE: [
                CallbackQueryHandler(goods_func_route, pattern='^' + '(添加商品|删除商品|上/下架)' + '$'),
            ],
            ADMIN_GOODS_STEP1: [
                CallbackQueryHandler(goods_func_step1, pattern='.*?')
            ],
            ADMIN_GOODS_STEP2: [
                CommandHandler('{}'.format(ADMIN_COMMAND_QUIT), icancel),
                MessageHandler(Filters.text, goods_func_exec),
                CallbackQueryHandler(goods_func_set_status, pattern='^' + '(上架|下架)' + '$'),
                CallbackQueryHandler(goods_func_step2, pattern='.*?')
            ],
            ADMIN_CARD_ROUTE: [
                CallbackQueryHandler(card_func_route, pattern='^' + '(添加卡密|删除卡密)' + '$'),
            ],
            ADMIN_CARD_STEP1: [
                CommandHandler('{}'.format(ADMIN_COMMAND_QUIT), icancel),
                CallbackQueryHandler(card_func_step1, pattern='.*?')
            ],
            ADMIN_CARD_STEP2: [
                CommandHandler('{}'.format(ADMIN_COMMAND_QUIT), icancel),
                MessageHandler(Filters.document, card_add_exec),
                CallbackQueryHandler(card_func_step2, pattern='.*?')
            ],
            ADMIN_TRADE_ROUTE: [
                CallbackQueryHandler(trade_func_route, pattern='^' + '(查询订单|重新激活订单)' + '$'),
            ],
            ADMIN_TRADE_EXEC: [
                MessageHandler(Filters.text, admin_trade_func_exec)
            ],
        },
        conversation_timeout=20,
        fallbacks=[CommandHandler('{}'.format(ADMIN_COMMAND_QUIT), icancel)]
    )

    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ROUTE: [
                CallbackQueryHandler(category_filter, pattern='^' + str('购买商品') + '$'),
                CallbackQueryHandler(trade_filter, pattern='^' + str('查询订单') + '$'),
            ],
            CATEGORY: [
                CallbackQueryHandler(goods_filter, pattern='.*?'),
            ],
            PRICE: [
                CallbackQueryHandler(user_price_filter, pattern='.*?'),
            ],
            SUBMIT: [
                CallbackQueryHandler(submit_trade, pattern='^' + str('提交订单') + '$'),
                CallbackQueryHandler(cancel_trade, pattern='^' + str('下次一定') + '$')
            ],
            TRADE: [
                MessageHandler(Filters.text, trade_query)
            ],
        },
        conversation_timeout=20,
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(admin_handler)

    updater.start_polling()
    updater.idle()


# -----------------------管理员函数区域-------------------------------
# -----------------------管理员函数区域-------------------------------


def admin(update, context):
    if is_admin(update, context):
        print('进入管理员函数')
        keyboard = [
            [
                InlineKeyboardButton("分类", callback_data=str('分类')),
                InlineKeyboardButton("商品", callback_data=str('商品')),
                InlineKeyboardButton("卡密", callback_data=str('卡密')),
                InlineKeyboardButton("订单", callback_data=str('订单'))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            '选择您的操作对象：',
            reply_markup=reply_markup
        )
        return ADMIN_ROUTE


def admin_entry_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '分类':
        keyboard = [
            [
                InlineKeyboardButton("添加分类", callback_data=str('添加分类')),
                InlineKeyboardButton("删除分类", callback_data=str('删除分类')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择分类指令：",
            reply_markup=reply_markup
        )
        return ADMIN_CATEGORY_ROUTE
    elif update.callback_query.data == '商品':
        keyboard = [
            [
                InlineKeyboardButton("添加商品", callback_data=str('添加商品')),
                InlineKeyboardButton("删除商品", callback_data=str('删除商品')),

            ],
            [
                InlineKeyboardButton("上/下架", callback_data=str('上/下架')),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择商品指令：",
            reply_markup=reply_markup
        )
        return ADMIN_GOODS_ROUTE
    elif update.callback_query.data == '卡密':
        keyboard = [
            [
                InlineKeyboardButton("添加卡密", callback_data=str('添加卡密')),
                InlineKeyboardButton("删除卡密", callback_data=str('删除卡密')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择卡密指令：",
            reply_markup=reply_markup
        )
        return ADMIN_CARD_ROUTE
    elif update.callback_query.data == '订单':
        keyboard = [
            [
                InlineKeyboardButton("查询订单", callback_data=str('查询订单')),
                InlineKeyboardButton("重新激活订单", callback_data=str('重新激活订单')),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择分类指令：",
            reply_markup=reply_markup
        )
        return ADMIN_TRADE_ROUTE


def category_func_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '添加分类':
        context.user_data['func'] = '添加分类'
        query.edit_message_text(text='请输入需要添加的分类名：')
        return CATEGORY_FUNC_EXEC
    elif update.callback_query.data == '删除分类':
        context.user_data['func'] = '删除分类'
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from category ORDER BY priority")
        categorys = cursor.fetchall()
        conn.close()
        if len(categorys) == 0:
            query.edit_message_text(text="您还没有添加分类", )
            return ConversationHandler.END
        for i in categorys:
            category_list = []
            print(i[1])
            category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
            keyboard.append(category_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="选择需要删除的分类",
            reply_markup=reply_markup
        )
        return CATEGORY_FUNC_EXEC


def category_func_exec(update, context):
    func = context.user_data['func']
    if func == '添加分类':
        category_name = update.message.text
        context.user_data['category_name'] = category_name
        print(category_name)
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from category where name=?", (category_name,))
        category_list = cursor.fetchone()
        conn.close()
        if category_list is None:
            context.user_data['func'] = '设置优先级'
            update.message.reply_text('请设置分类展示优先级，数字越小排名越靠前')
            return CATEGORY_FUNC_EXEC
        else:
            update.message.reply_text('分类名不能重复，请检查后重新输入。重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
    elif func == '设置优先级':
        priority = update.message.text
        category_name = context.user_data['category_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO category VALUES (NULL,?,?)", (category_name, priority))
        conn.commit()
        conn.close()
        update.message.reply_text('分类添加成功，会话已退出。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    elif func == '删除分类':
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        print("需要删除的分类名：" + category_name)
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=?", (category_name,))
        goods_list = cursor.fetchone()
        conn.close()
        if goods_list is None:
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM category WHERE name=?", (category_name,))
            conn.commit()
            conn.close()
            query.edit_message_text(
                text='分类*{}*删除成功！重启会话 /{}'.format(category_name, ADMIN_COMMAND_START),
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        else:
            query.edit_message_text(
                text='分类*{}*下存在商品，请删除该分类下所有商品后重试！重启会话 /{}'.format(category_name, ADMIN_COMMAND_START),
                parse_mode='Markdown'
            )
            return ConversationHandler.END


def goods_func_route(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    if len(categorys) == 0:
        query.edit_message_text(text='您还没有添加分类。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    for i in categorys:
        category_list = []
        category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query.data == '添加商品':
        context.user_data['func'] = '添加商品'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '删除商品':
        context.user_data['func'] = '删除商品'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1
    elif update.callback_query.data == '上/下架':
        context.user_data['func'] = '上/下架'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_GOODS_STEP1


def goods_func_step1(update, context):
    print('进入 goods_func_step1')
    try:
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        context.user_data['category_name'] = category_name
        func = context.user_data['func']
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? ORDER BY priority", (category_name,))
        goods = cursor.fetchall()
        conn.close()
        for i in goods:
            goods_list = [InlineKeyboardButton(i[2], callback_data=str(i[2]))]
            keyboard.append(goods_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        if func == '添加商品':
            query.edit_message_text(text='请输入需要添加的商品名称：')
            return ADMIN_GOODS_STEP2
        elif func == '删除商品':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要删除的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
        elif func == '上/下架':
            if len(goods) == 0:
                query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
                return ConversationHandler.END
            query.edit_message_text(text="选择需要更改上架状态的商品", reply_markup=reply_markup)
            return ADMIN_GOODS_STEP2
    except Exception as e:
        print(e)


def goods_func_step2(update, context):
    query = update.callback_query
    query.answer()
    goods_name = update.callback_query.data
    context.user_data['goods_name'] = goods_name
    category_name = context.user_data['category_name']
    func = context.user_data['func']
    if func == '删除商品':
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
        goods = cursor.fetchone()
        goods_id = goods[0]
        cursor.execute("select * from cards where goods_id=?", (goods_id,))
        card = cursor.fetchone()
        try:
            if card is None:
                cursor.execute("DELETE FROM goods WHERE id=?", (goods_id,))
                conn.commit()
                conn.close()
                query.edit_message_text(text='{}, {}已删除'.format(category_name, goods_name))
                return ConversationHandler.END
            else:
                conn.close()
                query.edit_message_text(text='{}, {} 下存在未删除卡密，请删除该商品全部卡密后重试。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                return ConversationHandler.END
        except Exception as e:
            print(e)
    elif func == '上/下架':
        keyboard = [
            [InlineKeyboardButton("上架", callback_data=str('上架')),
             InlineKeyboardButton("下架", callback_data=str('下架'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="您即将修改 {} 下 {} 的上下架状态，请选择：".format(category_name, goods_name),
                                reply_markup=reply_markup)
        return ADMIN_GOODS_STEP2


def goods_func_exec(update, context):
    category_name = context.user_data['category_name']
    func = context.user_data['func']
    if func == '添加商品':
        goods_name = update.message.text
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
        goods_list = cursor.fetchone()
        conn.close()
        if goods_list is None:
            context.user_data['goods_name'] = goods_name
            context.user_data['func'] = '设置价格'
            update.message.reply_text('请为 {} 设置价格：'.format(goods_name))
            return ADMIN_GOODS_STEP2
        else:
            update.message.reply_text(
                '分类 {} 下存在同名商品 {}，请检查后重试。重启会话 /{}'.format(category_name, goods_name, ADMIN_COMMAND_START))
            return ConversationHandler.END
    elif func == '设置价格':
        goods_price = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['goods_price'] = goods_price
        context.user_data['func'] = '设置描述'
        update.message.reply_text('请为 {} 设置描述：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置描述':
        description = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['description'] = description
        context.user_data['func'] = '设置使用方法'
        update.message.reply_text('请为 {} 设置使用方法：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置使用方法':
        use_way = update.message.text
        goods_name = context.user_data['goods_name']
        context.user_data['use_way'] = use_way
        context.user_data['func'] = '设置优先级'
        update.message.reply_text('请为 {} 设置展示优先级，数字越小越靠前：'.format(goods_name))
        return ADMIN_GOODS_STEP2
    elif func == '设置优先级':
        try:
            priority = update.message.text
            use_way = context.user_data['use_way']
            goods_name = context.user_data['goods_name']
            goods_price = context.user_data['goods_price']
            description = context.user_data['description']
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            print(category_name)
            cursor.execute("INSERT INTO goods VALUES (NULL,?,?,?,?,?,?,?)",
                           (category_name, goods_name, goods_price, 'active', description, use_way, priority))
            conn.commit()
            conn.close()
            update.message.reply_text('商品 {} 添加成功 重启会话 /{}'.format(goods_name, ADMIN_COMMAND_START))
            return ConversationHandler.END
        except Exception as e:
            print(e)
    elif func == '更改价格':
        price = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set price=? where category_name=? and name=?",
                       (price, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 价格更新成功，修改后的价格为：{} 重启会话 /{}'.format(
            category_name, goods_name, price, ADMIN_COMMAND_START))
        return ConversationHandler.END
    elif func == '更改描述':
        discription = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set description=? where category_name=? and name=?",
                       (discription, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 描述更新成功，修改后的描述为：{}'.format(category_name, goods_name, discription))
        return ConversationHandler.END
    elif func == '更改使用方法':
        use_way = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set use_way=? where category_name=? and name=?",
                       (use_way, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 使用方法更新成功，修改后的使用方法为：{}'.format(category_name, goods_name, use_way))
        return ConversationHandler.END
    elif func == '更改展示优先级':
        priority = update.message.text
        goods_name = context.user_data['goods_name']
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("update goods set priority=? where category_name=? and name=?",
                       (priority, category_name, goods_name))
        conn.commit()
        conn.close()
        update.message.reply_text(' {} 下 {} 使用方法更新成功，修改后的优先级为：{}'.format(category_name, goods_name, priority))
        return ConversationHandler.END


def goods_func_set_status(update, context):
    query = update.callback_query
    query.answer()
    goods_status = update.callback_query.data
    category_name = context.user_data['category_name']
    goods_name = context.user_data['goods_name']
    func = context.user_data['func']
    if func == '上/下架':
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
        goods = cursor.fetchone()
        now_goods_status = goods[4]
        if goods_status == '上架':
            if now_goods_status == 'active':
                query.edit_message_text('分类 {} 下 {} 的状态已经是上架状态，无需变动。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                conn.close()
                return ConversationHandler.END
            else:
                cursor.execute("update goods set status=? where category_name=? and name=?",
                               ('active', category_name, goods_name,))
                conn.commit()
                conn.close()
                query.edit_message_text('已将分类 {} 下 {} 的状态修改为上架'.format(category_name, goods_name))
                return ConversationHandler.END
        else:
            if now_goods_status == 'deactive':
                query.edit_message_text('分类 {} 下 {} 的状态已经是下架状态，无需变动。重启会话 /{}'.format(
                    category_name, goods_name, ADMIN_COMMAND_START))
                conn.close()
                return ConversationHandler.END
            else:
                cursor.execute("update goods set status=? where category_name=? and name=?",
                               ('deactive', category_name, goods_name,))
                conn.commit()
                conn.close()
                query.edit_message_text('已将分类 {} 下 {} 的状态修改为下架'.format(category_name, goods_name))
                return ConversationHandler.END


def card_func_route(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    if len(categorys) == 0:
        query.edit_message_text(text='您还没有添加分类。重启会话 /{}'.format(ADMIN_COMMAND_START))
        return ConversationHandler.END
    for i in categorys:
        category_list = []
        category_list.append(InlineKeyboardButton(i[1], callback_data=str(i[1])))
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query.data == '添加卡密':
        context.user_data['func'] = '添加卡密'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_CARD_STEP1
    elif update.callback_query.data == '删除卡密':
        context.user_data['func'] = '删除卡密'
        query.edit_message_text(text='请选择需要操作的分类：', reply_markup=reply_markup)
        return ADMIN_CARD_STEP1


def card_func_step1(update, context):
    print('进入 card_func_exec')
    try:
        query = update.callback_query
        query.answer()
        category_name = update.callback_query.data
        context.user_data['category_name'] = category_name
        func = context.user_data['func']
        keyboard = []
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from goods where category_name=? ORDER BY priority", (category_name,))
        goods = cursor.fetchall()
        conn.close()
        if len(goods) == 0:
            query.edit_message_text(text='该分类下没有商品。重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
        for i in goods:
            goods_list = [InlineKeyboardButton(i[2], callback_data=str(i[2]))]
            keyboard.append(goods_list)
        reply_markup = InlineKeyboardMarkup(keyboard)
        if func == '添加卡密':
            query.edit_message_text(text="选择需要添加卡密的商品", reply_markup=reply_markup)
            return ADMIN_CARD_STEP2
        elif func == '删除卡密':
            query.edit_message_text(
                text="选择需要删除卡密的商品\n"
                     "*注意：点击后卡密直接删除，稍后会将备份的卡密通过窗口发送给您!!!*",
                parse_mode='Markdown',
                reply_markup=reply_markup)
            return ADMIN_CARD_STEP2
    except Exception as e:
        print(e)


def card_func_step2(update, context):
    try:
        query = update.callback_query
        query.answer()
        goods_name = update.callback_query.data
        context.user_data['goods_name'] = goods_name
        category_name = context.user_data['category_name']
        func = context.user_data['func']
        if func == '添加卡密':
            query.edit_message_text(
                text='请发送文件名为: *分类名_商品名.txt* 的TXT文件\n'
                     '文件内容为卡密，一行一个\n',
                parse_mode='Markdown', )
            return ADMIN_CARD_STEP2
        elif func == '删除卡密':
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
            goods = cursor.fetchone()
            goods_id = goods[0]
            cursor.execute("select * from cards where goods_id=?", (goods_id,))
            cards_list = cursor.fetchall()
            if len(cards_list) == 0:
                conn.close()
                query.edit_message_text(text=" {} 下 {} 不存在卡密".format(category_name, goods_name))
                return ConversationHandler.END
            else:
                new_file = open('./card/导出卡密|{}|{}.txt'.format(category_name, goods_name), 'w')
                for card in cards_list:
                    context = card[3]
                    new_file.write(context + '\n')
                new_file.close()
                cursor.execute("delete from cards where goods_id=?", (goods_id,))
                conn.commit()
                conn.close()
                chat_id = query.message.chat.id
                bot.send_document(chat_id=chat_id, document=open(
                    './card/导出卡密|{}|{}.txt'.format(category_name, goods_name), 'rb'))
                os.remove('./card/导出卡密|{}|{}.txt'.format(category_name, goods_name))
                query.edit_message_text(text="分类 {} 下 {} 卡密已全部删除".format(category_name, goods_name))
                return ConversationHandler.END
    except Exception as e:
        print(e)


def card_add_exec(update, context):
    try:
        category_name = context.user_data['category_name']
        goods_name = context.user_data['goods_name']
        file_id = update.message.document.file_id
        new_file = bot.get_file(file_id)
        file_name = update.message.document.file_name
        new_file.download(custom_path='./card/{}'.format(file_name))
        split_file_name = file_name.split('.')[0]
        user_file_category_name = split_file_name.split('_')[0]
        user_file_goods_name = split_file_name.split('_')[1]
        print(category_name + "_" + goods_name)
        if user_file_category_name != category_name or user_file_goods_name != goods_name:
            update.message.reply_text('文件名有误，请检查后重新发送！重启会话 /{}'.format(ADMIN_COMMAND_START))
            return ConversationHandler.END
        else:
            f = open("./card/{}".format(file_name))
            card_list = []
            while True:
                lines = f.readlines(10000)
                if not lines:
                    break
                for line in lines:
                    card_list.append(line)
            new_card_list = []
            for card in card_list[:-1]:
                new_card_list.append(card[:-1])
            new_card_list.append(card_list[-1])
            f.close()
            os.remove('./card/{}'.format(file_name))
            print(new_card_list)
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name))
            goods = cursor.fetchone()
            goods_id = goods[0]
            for i in new_card_list:
                cursor.execute("INSERT INTO cards VALUES (NULL,?,?,?)", ('active', goods_id, i))
            conn.commit()
            conn.close()
            update.message.reply_text('卡密添加成功')
            return ConversationHandler.END
    except Exception as e:
        print(e)


def trade_func_route(update, context):
    query = update.callback_query
    query.answer()
    if update.callback_query.data == '查询订单':
        context.user_data['func'] = '查询订单'
        query.edit_message_text(text="请回复您需要查询的订单号：")
        return ADMIN_TRADE_EXEC
    elif update.callback_query.data == '重新激活订单':
        context.user_data['func'] = '重新激活订单'
        query.edit_message_text(text="请回复您需要重新激活的订单号：")
        return ADMIN_TRADE_EXEC


def admin_trade_func_exec(update, context):
    try:
        trade_id = update.message.text
        print(trade_id)
        func = context.user_data['func']
        print(func)
        if func == '查询订单':
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute('select * from trade where trade_id=?', (trade_id,))
            trade_list = cursor.fetchone()
            conn.close()
            if trade_list is None:
                update.message.reply_text('订单号有误，请确认后输入！')
                return ConversationHandler.END
            else:
                if trade_list[10] == 'paid':
                    status = '已支付'
                elif trade_list[10] == 'locking':
                    status = '已锁定'
                elif trade_list[10] == 'unpaid':
                    status = '未支付'
                goods_name = trade_list[2]
                description = trade_list[3]
                username = trade_list[8]
                card_context = trade_list[6]
                use_way = trade_list[4]
                trade_id = trade_list[0]
                update.message.reply_text(
                    '*订单查询成功*!\n'
                    '订单号：`{}`\n'
                    '订单状态：{}\n'
                    '下单用户：@{}\n'
                    '卡密内容：`{}`\n'
                    '描述：*{}*\n'
                    '使用方法：*{}*'.format(trade_id, status, username, card_context, description, use_way),
                    parse_mode='Markdown',
                )
                return ConversationHandler.END
        elif func == '重新激活订单':
            now_time = int(time.time())
            print(now_time)
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from trade where trade_id=?", (trade_id,))
            trade = cursor.fetchone()
            card_content = trade[6]
            cursor.execute("select * from trade where card_contents=? and status=?", (card_content, 'paid'))
            paid_trade = cursor.fetchone()
            print(paid_trade)
            if paid_trade is not None:
                update.message.reply_text('该卡密已被其他用户抢购，无法重新激活轮询！')
                return ConversationHandler.END
            else:
                cursor.execute('update trade set creat_time=? where trade_id=?', (now_time, trade_id,))
                cursor.execute('update trade set status=? where trade_id=?', ('unpaid', trade_id,))
                conn.commit()
                conn.close()
                update.message.reply_text('该订单已经重新放入轮询队列')
                return ConversationHandler.END
    except Exception as e:
        print(e)


def is_admin(update, context):
    if update.message.from_user.id in ADMIN_ID:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='*非管理员，无权操作*',
            parse_mode='Markdown'
        )
        return False


def get_trade_id():
    now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(0, 99)
    if random_num <= 10:
        random_num = str(0) + str(random_num)
    unique_num = str(now_time) + str(random_num)
    return unique_num


def icancel(update, context):
    update.message.reply_text('期待再次见到你～ /{}'.format(ADMIN_COMMAND_START))
    return ConversationHandler.END


# -----------------------用户函数区域-------------------------------
# -----------------------用户函数区域-------------------------------


def start(update, context):
    print('进入start函数')
    keyboard = [
        [InlineKeyboardButton("购买商品", callback_data=str('购买商品')),
         InlineKeyboardButton("查询订单", callback_data=str('查询订单'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        '本系统为毒液论坛积分自助购买机器人，如发现未正常回调请联系小助理:@duyeikfBot',
        reply_markup=reply_markup
    )
    return ROUTE


def category_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from category ORDER BY priority")
    categorys = cursor.fetchall()
    conn.close()
    for i in categorys:
        category_list = [InlineKeyboardButton(i[1], callback_data=str(i[1]))]
        keyboard.append(category_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="请选择你要充值的积分数量",
        reply_markup=reply_markup
    )
    return CATEGORY


def goods_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    category_name = update.callback_query.data
    context.user_data['category_name'] = category_name
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where category_name=? and status=? ORDER BY priority",
                   (category_name, 'active',))
    goods = cursor.fetchall()
    for i in goods:
        goods_id = i[0]
        cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
        active_cards = cursor.fetchall()
        cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'locking'))
        locking_cards = cursor.fetchall()
        goods_list = [InlineKeyboardButton(i[2] + ' | 库存:{} | 交易中:{}'.format(len(active_cards), len(locking_cards)),
                                           callback_data=str(i[2]))]
        keyboard.append(goods_list)
    conn.close()
    reply_markup = InlineKeyboardMarkup(keyboard)
    if len(goods) == 0:
        query.edit_message_text(text="该分类下暂时还没有商品 主菜单: /start \n")
        return ConversationHandler.END
    else:
        query.edit_message_text(
            text="选择您要购买的积分数量：\n"
                 "库存：当前可购买的积分数量\n"
                 "交易中：目前其他用户正在购买中，10min不付款将释放订单",
            reply_markup=reply_markup)
        return PRICE


def user_price_filter(update, context):
    query = update.callback_query
    query.answer()
    goods_name = update.callback_query.data
    category_name = context.user_data['category_name']
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from goods where category_name=? and name=?", (category_name, goods_name,))
    goods = cursor.fetchone()
    goods_id = goods[0]
    cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
    active_cards = cursor.fetchall()
    cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'locking'))
    locking_cards = cursor.fetchall()
    conn.close()
    if len(active_cards) == 0 and len(locking_cards) != 0:
        query.edit_message_text(text="该商品暂时*无库存*\n"
                                     "现在有人*正在交易*，如果超时未支付，该订单将会被释放，届时即可购买\n"
                                     "会话已结束，使用 /start 重新发起会话")
        return ConversationHandler.END
    elif len(active_cards) == 0 and len(locking_cards) == 0:
        query.edit_message_text(text="该商品暂时*无库存*，等待补货\n"
                                     "会话已结束，使用 /start 重新发起会话",
                                parse_mode='Markdown', )
        return ConversationHandler.END
    elif len(active_cards) > 0:
        price = goods[3]
        descrip = goods[5]
        context.user_data['goods_id'] = goods_id
        context.user_data['goods_name'] = goods_name
        context.user_data['price'] = price
        keyboard = [
            [InlineKeyboardButton("提交订单", callback_data=str('提交订单')),
             InlineKeyboardButton("取消订单", callback_data=str('取消订单'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="积分数量：*{}*\n"
                 "价格：*{}*\n"
                 "介绍：*{}*\n".format(goods_name, price, descrip),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return SUBMIT


def submit_trade(update, context):
    query = update.callback_query
    query.answer()
    user = update.callback_query.message.chat
    user_id = user.id
    username = user.username
    try:
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where user_id=? and status=?", (user_id, 'unpaid'))
        trade_list = cursor.fetchone()
        print(trade_list)
        conn.close()
        if trade_list is None:
            goods_name = context.user_data['goods_name']
            goods_id = context.user_data['goods_id']
            category_name = context.user_data['category_name']
            price = context.user_data['price']
            name = category_name + "|" + goods_name
            trade_id = get_trade_id()
            print('商品名：{}，价格：{}，交易ID：{}'.format(name, price, trade_id))
            conn = sqlite3.connect('faka.sqlite3')
            cursor = conn.cursor()
            cursor.execute("select * from goods where id=?", (goods_id,))
            goods_info = cursor.fetchone()
            description = goods_info[5]
            use_way = goods_info[6]
            cursor.execute("select * from cards where goods_id=? and status=?", (goods_id, 'active'))
            card_info = cursor.fetchone()
            card_id = card_info[0]
            card_content = card_info[3]
            conn.close()
            now_time = int(time.time())
            trade_data = make_data_dict(price, name, trade_id)
            pay_url = epay_submit(trade_data)
            if pay_url != 'API请求失败':
                print('API请求成功，已成功返回支付链接')
                conn = sqlite3.connect('faka.sqlite3')
                cursor = conn.cursor()
                cursor.execute("update cards set status=? where id=?", ('locking', card_id,))
                cursor.execute("INSERT INTO trade VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                               (trade_id, goods_id, category_name + "｜" + goods_name, description, use_way, card_id,
                                card_content, user_id, username, now_time, 'unpaid',pay_url))
                conn.commit()
                conn.close()
                keyboard = [[InlineKeyboardButton("点击跳转支付", url=pay_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(
                    '请在{}s内支付完成，超时支付会导致发货失败！\n'
                    '[点击这里]({})跳转支付，或者点击下方跳转按钮'.format(PAY_TIMEOUT, pay_url),
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            return ConversationHandler.END
        else:
            query.edit_message_text('您存在未支付订单，请支付或等待订单过期后重试！')
            return ConversationHandler.END
    except Exception as e:
        print(e)


def cancel_trade(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="记得哦～下次一定")
    return ConversationHandler.END


def trade_filter(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="请回复您需要查询的订单号：")
    return TRADE


def trade_query(update, context):
    trade_id = update.message.text
    user = update.message.from_user
    user_id = user.id
    conn = sqlite3.connect('faka.sqlite3')
    cursor = conn.cursor()
    cursor.execute('select * from trade where trade_id=? and user_id=?', (trade_id, user_id,))
    trade_list = cursor.fetchone()
    conn.close()
    if trade_list is None:
        update.message.reply_text('订单号有误，请确认后输入！')
        return ConversationHandler.END
    elif trade_list[10] == 'locking':
        goods_name = trade_list[2]
        description = trade_list[3]
        trade_id = trade_list[0]
        update.message.reply_text(
            '*订单查询成功*!\n'
            '订单号：`{}`\n'
            '订单状态：*已取消*\n'
            '原因：*逾期未付*'.format(trade_id),
            parse_mode='Markdown',
        )
        return ConversationHandler.END
    elif trade_list[10] == 'paid':
        trade_id = trade_list[0]
        goods_name = trade_list[2]
        description = trade_list[3]
        use_way = trade_list[4]
        card_context = trade_list[6]
        update.message.reply_text(
            '*订单查询成功*!\n'
            '订单号：`{}`\n'
            '商品：*{}*\n'
            '描述：*{}*\n'
            '卡密内容：`{}`\n'
            '使用方法：*{}*\n'.format(trade_id, goods_name, description, card_context, use_way),
            parse_mode='Markdown',
        )
        return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('期待再次见到你～')
    return ConversationHandler.END


def check_trade():
    while True:
        print('---------------订单轮询开始---------------')
        conn = sqlite3.connect('faka.sqlite3')
        cursor = conn.cursor()
        cursor.execute("select * from trade where status=?", ('unpaid',))
        unpaid_list = cursor.fetchall()
        conn.close()
        for i in unpaid_list:
            now_time = int(time.time())
            trade_id = i[0]
            print(trade_id)
            user_id = i[7]
            creat_time = i[9]
            goods_name = i[2]
            description = i[3]
            use_way = i[4]
            card_context = i[6]
            card_id = i[5]
            sub_time = now_time - int(creat_time)
            print(sub_time)
            if sub_time >= PAY_TIMEOUT:
                conn = sqlite3.connect('faka.sqlite3')
                cursor = conn.cursor()
                cursor.execute("update trade set status=? where trade_id=?", ('locking', trade_id,))
                cursor.execute("update cards set status=? where id=?", ('active', card_id,))
                conn.commit()
                conn.close()
                bot.send_message(
                    chat_id=user_id,
                    text='很遗憾，订单已关闭\n'
                         '订单号：`{}`\n'
                         '原因：逾期未付\n'.format(trade_id),
                    parse_mode='Markdown',
                )
            else:
                try:
                    rst = check_status(trade_id)
                    if rst == '支付成功':
                        conn = sqlite3.connect('faka.sqlite3')
                        cursor = conn.cursor()
                        cursor.execute("update trade set status=? where trade_id=?", ('paid', trade_id,))
                        cursor.execute("DELETE FROM cards WHERE id=?", (card_id,))
                        conn.commit()
                        conn.close()
                        bot.send_message(
                            chat_id=user_id,
                            text='恭喜！订单支付成功!\n'
                                 '订单号：`{}`\n'
                                 '商品：*{}*\n'
                                 '描述：*{}*\n'
                                 '卡密内容：`{}`\n'
                                 '使用方法：*{}*\n'.format(trade_id, goods_name, description, card_context, use_way),
                            parse_mode='Markdown',
                        )
                except Exception as e:
                    print(e)
            time.sleep(3)
        print('---------------订单轮询结束---------------')
        time.sleep(10)
