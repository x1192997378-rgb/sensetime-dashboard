from __future__ import annotations

from datetime import datetime, timedelta

import investpy
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

from data_pipeline import cron_integration_note, run_pipeline
from news_service import fetch_news

LANGS = {
    "zh-CN": "简体中文",
    "ja": "日本語",
    "en": "English",
    "th": "ไทย",
}

I18N = {
    "app_title": {
        "zh-CN": "单股票分析与实时行情作品集",
        "ja": "単一銘柄分析とリアルタイム相場ダッシュボード",
        "en": "Single-Stock Analysis and Realtime Dashboard",
        "th": "แดชบอร์ดวิเคราะห์หุ้นเดี่ยวและข้อมูลเรียลไทม์",
    },
    "app_caption": {
        "zh-CN": "默认示例：港股商汤-W（0020.HK）",
        "ja": "デフォルト例: 香港株 SenseTime-W (0020.HK)",
        "en": "Default sample: HK stock SenseTime-W (0020.HK)",
        "th": "ตัวอย่างเริ่มต้น: หุ้นฮ่องกง SenseTime-W (0020.HK)",
    },
    "language": {"zh-CN": "语言", "ja": "言語", "en": "Language", "th": "ภาษา"},
    "sidebar_header": {"zh-CN": "参数设置", "ja": "パラメータ設定", "en": "Parameters", "th": "พารามิเตอร์"},
    "market": {"zh-CN": "市场", "ja": "市場", "en": "Market", "th": "ตลาด"},
    "stock_code": {"zh-CN": "股票代码", "ja": "銘柄コード", "en": "Ticker", "th": "รหัสหุ้น"},
    "history_days": {"zh-CN": "历史天数", "ja": "履歴日数", "en": "History days", "th": "จำนวนวันย้อนหลัง"},
    "threshold_pct": {"zh-CN": "统计阈值（涨幅>%）", "ja": "閾値（上昇率>%）", "en": "Threshold (gain > %)", "th": "เกณฑ์สถิติ (เพิ่มขึ้น > %)"},
    "fund_quantile": {"zh-CN": "主力阈值分位数", "ja": "主力しきい値分位", "en": "Main-force quantile", "th": "ควอนไทล์เกณฑ์เงินทุนหลัก"},
    "news_keywords": {"zh-CN": "新闻关键词", "ja": "ニュースキーワード", "en": "News keywords", "th": "คีย์เวิร์ดข่าว"},
    "us_kline_interval": {"zh-CN": "美股K线周期", "ja": "米株K線足", "en": "US K-line interval", "th": "ช่วงเวลาแท่งเทียนหุ้นสหรัฐ"},
    "include_ext": {"zh-CN": "美股K线包含盘前盘后", "ja": "時間外を含める", "en": "Include pre/post market", "th": "รวมก่อน/หลังตลาด"},
    "auto_refresh": {"zh-CN": "美股扩展自动刷新", "ja": "米株拡張の自動更新", "en": "Auto refresh US panel", "th": "รีเฟรชหน้า US อัตโนมัติ"},
    "auto_refresh_sec": {"zh-CN": "自动刷新间隔(秒)", "ja": "自動更新間隔（秒）", "en": "Auto refresh interval (sec)", "th": "ช่วงเวลารีเฟรชอัตโนมัติ (วินาที)"},
    "run_history": {"zh-CN": "运行历史分析", "ja": "履歴分析を実行", "en": "Run historical analysis", "th": "รันวิเคราะห์ย้อนหลัง"},
    "refresh_realtime": {"zh-CN": "刷新实时行情", "ja": "リアルタイム更新", "en": "Refresh realtime", "th": "รีเฟรชเรียลไทม์"},
    "refresh_quote": {"zh-CN": "刷新实时报价", "ja": "気配値を更新", "en": "Refresh quote", "th": "รีเฟรชราคา"},
    "refresh_us": {"zh-CN": "刷新美股扩展", "ja": "米株拡張を更新", "en": "Refresh US panel", "th": "รีเฟรชหน้า US"},
    "refresh_news": {"zh-CN": "刷新新闻", "ja": "ニュース更新", "en": "Refresh news", "th": "รีเฟรชข่าว"},
    "tab_quote": {"zh-CN": "实时报价", "ja": "リアルタイム気配値", "en": "Realtime Quote", "th": "ราคาเรียลไทม์"},
    "tab_realtime": {"zh-CN": "实时资金", "ja": "リアルタイム資金", "en": "Realtime Flow", "th": "กระแสเงินเรียลไทม์"},
    "tab_us": {"zh-CN": "美股扩展", "ja": "米株拡張", "en": "US Extension", "th": "ส่วนขยายหุ้นสหรัฐ"},
    "tab_news": {"zh-CN": "时事新闻", "ja": "ニュース", "en": "News", "th": "ข่าว"},
    "tab_history": {"zh-CN": "历史分析", "ja": "履歴分析", "en": "Historical Analysis", "th": "วิเคราะห์ย้อนหลัง"},
    "market_hk": {"zh-CN": "港股", "ja": "香港株", "en": "Hong Kong", "th": "ฮ่องกง"},
    "market_us": {"zh-CN": "美股", "ja": "米国株", "en": "US", "th": "สหรัฐ"},
    "interval_1m": {"zh-CN": "1分钟", "ja": "1分", "en": "1m", "th": "1 นาที"},
    "interval_3m": {"zh-CN": "3分钟", "ja": "3分", "en": "3m", "th": "3 นาที"},
    "interval_15m": {"zh-CN": "15分钟", "ja": "15分", "en": "15m", "th": "15 นาที"},
    "interval_30m": {"zh-CN": "30分钟", "ja": "30分", "en": "30m", "th": "30 นาที"},
    "interval_60m": {"zh-CN": "1小时", "ja": "1時間", "en": "1h", "th": "1 ชั่วโมง"},
    "interval_1d": {"zh-CN": "1日", "ja": "1日", "en": "1d", "th": "1 วัน"},
    "pipeline_success": {
        "zh-CN": "数据流程已跑通：抓取 -> 清洗 -> 特征 -> 持久化 -> 展示",
        "ja": "データ処理が完了: 取得 -> クリーニング -> 特徴量 -> 永続化 -> 表示",
        "en": "Pipeline completed: fetch -> clean -> features -> persist -> display",
        "th": "ไปป์ไลน์เสร็จสิ้น: ดึงข้อมูล -> ทำความสะอาด -> สร้างคุณลักษณะ -> บันทึก -> แสดงผล",
    },
    "latest_close": {"zh-CN": "最新收盘价", "ja": "最新終値", "en": "Latest close", "th": "ราคาปิดล่าสุด"},
    "avg_return": {"zh-CN": "平均日回报率", "ja": "平均日次リターン", "en": "Avg daily return", "th": "ผลตอบแทนเฉลี่ยรายวัน"},
    "max_return": {"zh-CN": "最大日涨幅", "ja": "最大日次上昇率", "en": "Max daily gain", "th": "การขึ้นสูงสุดรายวัน"},
    "rise_ratio": {"zh-CN": "涨幅>{pct}%占比", "ja": "上昇率>{pct}%の比率", "en": "Days gain>{pct}% ratio", "th": "สัดส่วนวันที่ขึ้น>{pct}%"},
    "close_ma": {"zh-CN": "收盘价与均线", "ja": "終値と移動平均", "en": "Close and moving averages", "th": "ราคาปิดและเส้นค่าเฉลี่ย"},
    "amount_trend": {"zh-CN": "成交额趋势", "ja": "売買代金トレンド", "en": "Turnover trend", "th": "แนวโน้มมูลค่าการซื้อขาย"},
    "key_report": {"zh-CN": "关键报告", "ja": "主要レポート", "en": "Key report", "th": "รายงานสำคัญ"},
    "report_line1": {
        "zh-CN": "- 过去 {days} 天，平均日回报率为 **{avg:.2f}%**。",
        "ja": "- 過去 {days} 日の平均日次リターンは **{avg:.2f}%** です。",
        "en": "- Over the past {days} days, avg daily return is **{avg:.2f}%**.",
        "th": "- ในช่วง {days} วันที่ผ่านมา ผลตอบแทนเฉลี่ยรายวันคือ **{avg:.2f}%**",
    },
    "report_line2": {
        "zh-CN": "- 最大单日涨幅为 **{maxv:.2f}%**。",
        "ja": "- 最大日次上昇率は **{maxv:.2f}%** です。",
        "en": "- Maximum single-day gain is **{maxv:.2f}%**.",
        "th": "- การขึ้นสูงสุดในหนึ่งวันคือ **{maxv:.2f}%**",
    },
    "report_line3": {
        "zh-CN": "- 涨幅大于 **{pct:.1f}%** 的交易日占比为 **{ratio:.2f}%**。",
        "ja": "- 上昇率が **{pct:.1f}%** を超える日の比率は **{ratio:.2f}%** です。",
        "en": "- The ratio of days with gain > **{pct:.1f}%** is **{ratio:.2f}%**.",
        "th": "- สัดส่วนวันที่เพิ่มขึ้นเกิน **{pct:.1f}%** คือ **{ratio:.2f}%**",
    },
    "details_data": {"zh-CN": "明细数据（含清洗与指标）", "ja": "詳細データ（クリーニング/指標含む）", "en": "Detailed data (cleaned + features)", "th": "ข้อมูลรายละเอียด (ทำความสะอาด + ตัวชี้วัด)"},
    "persist_caption": {"zh-CN": "持久化输出：data/stock_history.csv 与 data/stock_history.db", "ja": "永続化出力: data/stock_history.csv と data/stock_history.db", "en": "Persisted output: data/stock_history.csv and data/stock_history.db", "th": "ไฟล์ผลลัพธ์ถาวร: data/stock_history.csv และ data/stock_history.db"},
    "run_failed": {"zh-CN": "运行失败：{err}", "ja": "実行失敗: {err}", "en": "Run failed: {err}", "th": "ทำงานล้มเหลว: {err}"},
    "click_run_tip": {"zh-CN": "点击左侧按钮开始运行数据流程。", "ja": "左側のボタンを押して実行してください。", "en": "Click the left button to start the pipeline.", "th": "กดปุ่มด้านซ้ายเพื่อเริ่มไปป์ไลน์"},
    "realtime_subheader": {"zh-CN": "英为财情资金快照（含延迟）", "ja": "Investing.com 資金スナップショット（遅延あり）", "en": "Investing.com flow snapshot (delayed)", "th": "สแนปชอตกระแสเงินจาก Investing.com (มีดีเลย์)"},
    "realtime_caption": {"zh-CN": "默认数据源为 Investing.com；失败时自动降级到 Yahoo。", "ja": "既定データソースは Investing.com。失敗時は Yahoo にフォールバックします。", "en": "Default source is Investing.com; fallback to Yahoo on failure.", "th": "แหล่งข้อมูลหลักคือ Investing.com; หากล้มเหลวจะสลับไป Yahoo"},
    "latest_price": {"zh-CN": "最新价", "ja": "最新値", "en": "Latest price", "th": "ราคาล่าสุด"},
    "chg_pct": {"zh-CN": "涨跌幅", "ja": "騰落率", "en": "Change %", "th": "การเปลี่ยนแปลง %"},
    "latest_1m_amount": {"zh-CN": "最新1分钟成交额", "ja": "直近1分売買代金", "en": "Latest 1m turnover", "th": "มูลค่าซื้อขาย 1 นาทีล่าสุด"},
    "main_share": {"zh-CN": "主力占比", "ja": "主力比率", "en": "Main-force share", "th": "สัดส่วนเงินทุนหลัก"},
    "current_source": {"zh-CN": "当前数据源：{src}", "ja": "現在のソース: {src}", "en": "Current source: {src}", "th": "แหล่งข้อมูลปัจจุบัน: {src}"},
    "main_flow": {"zh-CN": "主力资金", "ja": "主力資金", "en": "Main flow", "th": "กระแสเงินหลัก"},
    "retail_flow": {"zh-CN": "小散资金", "ja": "รายย่อย", "en": "Retail flow", "th": "กระแสเงินรายย่อย"},
    "flow_trend": {"zh-CN": "主力/小散资金趋势线", "ja": "主力/個人資金トレンド", "en": "Main/Retail flow trend", "th": "แนวโน้มเงินทุนหลัก/รายย่อย"},
    "time_axis": {"zh-CN": "时间", "ja": "時間", "en": "Time", "th": "เวลา"},
    "flow_scale": {"zh-CN": "资金规模", "ja": "資金規模", "en": "Flow scale", "th": "ขนาดเงินทุน"},
    "total_amount": {"zh-CN": "总成交额", "ja": "総売買代金", "en": "Total turnover", "th": "มูลค่าซื้อขายรวม"},
    "main_net": {"zh-CN": "主力净流入", "ja": "主力純流入", "en": "Main net inflow", "th": "เงินทุนหลักสุทธิไหลเข้า"},
    "retail_net": {"zh-CN": "小散净流入", "ja": "รายย่อยสุทธิไหลเข้า", "en": "Retail net inflow", "th": "รายย่อยสุทธิไหลเข้า"},
    "chart_order": {"zh-CN": "图表顺序：价格线图 -> 成交额线图 -> 主力/小散资金趋势线图 -> 主力净流入柱状图", "ja": "図の順序: 価格線 -> 売買代金線 -> 主力/個人資金トレンド -> 主力純流入バー", "en": "Chart order: price -> turnover -> main/retail trend -> main net bar", "th": "ลำดับกราฟ: ราคา -> มูลค่าซื้อขาย -> แนวโน้มหลัก/รายย่อย -> แท่งเงินทุนหลักสุทธิ"},
    "main_threshold": {"zh-CN": "主力判定阈值（分位数 {q:.2f}）：{v:,.2f}", "ja": "主力判定しきい値（分位 {q:.2f}）: {v:,.2f}", "en": "Main-force threshold (quantile {q:.2f}): {v:,.2f}", "th": "เกณฑ์เงินทุนหลัก (ควอนไทล์ {q:.2f}): {v:,.2f}"},
    "flow_warning": {"zh-CN": "主力/小散为分钟级估算口径，用于分析展示，不代表交易所官方统计。", "ja": "主力/個人の値は分足ベースの推定値であり、分析表示用です。", "en": "Main/Retail values are minute-level estimates for analysis only.", "th": "ค่าหลัก/รายย่อยเป็นค่าประมาณระดับนาทีเพื่อการวิเคราะห์เท่านั้น"},
    "realtime_failed": {"zh-CN": "实时行情拉取失败：{err}", "ja": "リアルタイム取得失敗: {err}", "en": "Realtime fetch failed: {err}", "th": "ดึงข้อมูลเรียลไทม์ล้มเหลว: {err}"},
    "quote_subheader": {"zh-CN": "实时报价", "ja": "リアルタイム気配値", "en": "Realtime Quote", "th": "ราคาเรียลไทม์"},
    "quote_caption": {"zh-CN": "用于快速查看当前价位与日内区间。", "ja": "現在値と日中レンジを素早く確認します。", "en": "Quick view of current price and intraday range.", "th": "ดูราคาปัจจุบันและช่วงราคาในวันแบบรวดเร็ว"},
    "day_high": {"zh-CN": "今日最高", "ja": "本日高値", "en": "Day high", "th": "สูงสุดวันนี้"},
    "day_low": {"zh-CN": "今日最低", "ja": "本日安値", "en": "Day low", "th": "ต่ำสุดวันนี้"},
    "day_open": {"zh-CN": "今开", "ja": "始値", "en": "Open", "th": "ราคาเปิด"},
    "prev_close": {"zh-CN": "昨收", "ja": "前日終値", "en": "Prev close", "th": "ปิดก่อนหน้า"},
    "quote_source_time": {"zh-CN": "数据源：{src} | 更新时间：{t}", "ja": "ソース: {src} | 更新: {t}", "en": "Source: {src} | Updated: {t}", "th": "แหล่งข้อมูล: {src} | อัปเดต: {t}"},
    "quote_failed": {"zh-CN": "实时报价获取失败：{err}", "ja": "気配値取得失敗: {err}", "en": "Quote fetch failed: {err}", "th": "ดึงราคาล้มเหลว: {err}"},
    "us_subheader": {"zh-CN": "美股盘前/盘后与实时K线", "ja": "米株の時間外とリアルタイムK線", "en": "US pre/post market and realtime K-line", "th": "ก่อน/หลังตลาดสหรัฐและแท่งเทียนเรียลไทม์"},
    "us_caption": {"zh-CN": "适用于 TSLA、AAPL、NVDA 等美股代码。", "ja": "TSLA、AAPL、NVDA など米国株コード向け。", "en": "For US tickers like TSLA, AAPL, NVDA.", "th": "สำหรับหุ้นสหรัฐ เช่น TSLA, AAPL, NVDA"},
    "switch_market_us": {"zh-CN": "请在左侧将市场切换为“美股”。", "ja": "左側で市場を「米国株」に切り替えてください。", "en": "Please switch market to US on the left.", "th": "กรุณาเปลี่ยนตลาดด้านซ้ายเป็น US"},
    "session_status": {"zh-CN": "交易时段状态", "ja": "取引セッション", "en": "Session status", "th": "สถานะช่วงการซื้อขาย"},
    "time_et": {"zh-CN": "美东时间", "ja": "米東時間", "en": "US/Eastern", "th": "เวลา US/Eastern"},
    "pre_market": {"zh-CN": "盘前", "ja": "プレ", "en": "Pre", "th": "ก่อนเปิด"},
    "after_market": {"zh-CN": "盘后", "ja": "アフター", "en": "Post", "th": "หลังปิด"},
    "update_et": {"zh-CN": "昨收：{p:.3f} | 更新时间：{t} (US/Eastern)", "ja": "前日終値: {p:.3f} | 更新: {t} (US/Eastern)", "en": "Prev close: {p:.3f} | Updated: {t} (US/Eastern)", "th": "ปิดก่อนหน้า: {p:.3f} | อัปเดต: {t} (US/Eastern)"},
    "kline": {"zh-CN": "K线", "ja": "K線", "en": "K-line", "th": "แท่งเทียน"},
    "rt_kline_title": {"zh-CN": "{sym} 实时K线 ({iv})", "ja": "{sym} リアルタイムK線 ({iv})", "en": "{sym} Realtime K-line ({iv})", "th": "{sym} แท่งเทียนเรียลไทม์ ({iv})"},
    "price_axis": {"zh-CN": "价格", "ja": "価格", "en": "Price", "th": "ราคา"},
    "us_failed": {"zh-CN": "美股扩展数据获取失败：{err}", "ja": "米株拡張データ取得失敗: {err}", "en": "US extension fetch failed: {err}", "th": "ดึงข้อมูลส่วนขยาย US ล้มเหลว: {err}"},
    "news_subheader": {"zh-CN": "商汤相关时事新闻", "ja": "SenseTime 関連ニュース", "en": "SenseTime related news", "th": "ข่าวที่เกี่ยวข้องกับ SenseTime"},
    "news_caption": {"zh-CN": "基于 Google News RSS 聚合，提供标题、来源、发布时间和情绪标签。", "ja": "Google News RSS を集約し、タイトル/ソース/時刻/感情を表示します。", "en": "Aggregated from Google News RSS with title/source/time/sentiment.", "th": "รวมจาก Google News RSS พร้อมหัวข้อ แหล่งที่มา เวลา และอารมณ์ข่าว"},
    "no_news": {"zh-CN": "暂无新闻结果，请调整关键词重试。", "ja": "ニュースがありません。キーワードを調整してください。", "en": "No news found. Try different keywords.", "th": "ไม่พบข่าว กรุณาลองคีย์เวิร์ดอื่น"},
    "bullish": {"zh-CN": "利好", "ja": "強気", "en": "Bullish", "th": "เชิงบวก"},
    "neutral": {"zh-CN": "中性", "ja": "中立", "en": "Neutral", "th": "เป็นกลาง"},
    "bearish": {"zh-CN": "利空", "ja": "弱気", "en": "Bearish", "th": "เชิงลบ"},
    "unknown_source": {"zh-CN": "未知来源", "ja": "不明ソース", "en": "Unknown source", "th": "ไม่ทราบแหล่งที่มา"},
    "all": {"zh-CN": "全部", "ja": "すべて", "en": "All", "th": "ทั้งหมด"},
    "source_filter": {"zh-CN": "来源筛选", "ja": "ソース絞り込み", "en": "Source filter", "th": "ตัวกรองแหล่งข่าว"},
    "sentiment_filter": {"zh-CN": "情绪筛选", "ja": "感情絞り込み", "en": "Sentiment filter", "th": "ตัวกรองอารมณ์ข่าว"},
    "no_news_filtered": {"zh-CN": "当前筛选条件下暂无新闻。", "ja": "現在の条件ではニュースがありません。", "en": "No news under current filters.", "th": "ไม่มีข่าวตามเงื่อนไขตัวกรอง"},
    "select_news": {"zh-CN": "选择一条新闻进行联动分析", "ja": "連動分析するニュースを選択", "en": "Select one news item for linkage analysis", "th": "เลือกข่าวหนึ่งรายการเพื่อวิเคราะห์เชื่อมโยง"},
    "current_event": {"zh-CN": "当前事件", "ja": "現在のイベント", "en": "Current event", "th": "เหตุการณ์ปัจจุบัน"},
    "source": {"zh-CN": "来源", "ja": "ソース", "en": "Source", "th": "แหล่งที่มา"},
    "time": {"zh-CN": "时间", "ja": "時刻", "en": "Time", "th": "เวลา"},
    "sentiment": {"zh-CN": "情绪", "ja": "感情", "en": "Sentiment", "th": "อารมณ์ข่าว"},
    "event_price_link": {"zh-CN": "新闻事件与价格联动", "ja": "ニュースイベントと価格連動", "en": "News event and price linkage", "th": "ความเชื่อมโยงข่าวกับราคา"},
    "news_event": {"zh-CN": "新闻事件", "ja": "ニュースイベント", "en": "News Event", "th": "เหตุการณ์ข่าว"},
    "event_base": {"zh-CN": "事件基准价", "ja": "イベント基準価格", "en": "Event base price", "th": "ราคาฐานเหตุการณ์"},
    "after_1h": {"zh-CN": "事件后1h", "ja": "イベント後1h", "en": "After 1h", "th": "หลังเหตุการณ์ 1h"},
    "after_4h": {"zh-CN": "事件后4h", "ja": "イベント後4h", "en": "After 4h", "th": "หลังเหตุการณ์ 4h"},
    "after_1d": {"zh-CN": "事件后1d", "ja": "イベント後1d", "en": "After 1d", "th": "หลังเหตุการณ์ 1d"},
    "news_capture_time": {"zh-CN": "新闻抓取时间：{t}", "ja": "ニュース取得時刻: {t}", "en": "News captured at: {t}", "th": "เวลาที่ดึงข่าว: {t}"},
    "news_failed": {"zh-CN": "新闻拉取失败：{err}", "ja": "ニュース取得失敗: {err}", "en": "News fetch failed: {err}", "th": "ดึงข่าวล้มเหลว: {err}"},
    "err_no_realtime_data": {"zh-CN": "英为财情和 Yahoo 均未返回可用实时数据。", "ja": "Investing.com と Yahoo の両方で有効データがありません。", "en": "Neither Investing.com nor Yahoo returned usable realtime data.", "th": "ทั้ง Investing.com และ Yahoo ไม่ได้ส่งข้อมูลเรียลไทม์ที่ใช้ได้"},
    "err_no_quote": {"zh-CN": "无法获取实时报价数据。", "ja": "リアルタイム気配値を取得できません。", "en": "Unable to fetch realtime quote.", "th": "ไม่สามารถดึงราคาเรียลไทม์ได้"},
    "err_no_us_session": {"zh-CN": "无法获取美股盘前/盘后数据。", "ja": "米株の時間外データを取得できません。", "en": "Unable to fetch US pre/post market data.", "th": "ไม่สามารถดึงข้อมูลก่อน/หลังตลาดสหรัฐได้"},
    "err_no_3m_base": {"zh-CN": "无法获取3分钟K线基础数据。", "ja": "3分足の基礎データを取得できません。", "en": "Unable to fetch 3m K-line base data.", "th": "ไม่สามารถดึงข้อมูลพื้นฐานแท่ง 3 นาทีได้"},
    "err_no_kline": {"zh-CN": "无法获取 {interval} K线数据。", "ja": "{interval} K線データを取得できません。", "en": "Unable to fetch {interval} K-line data.", "th": "ไม่สามารถดึงข้อมูลแท่ง {interval} ได้"},
    "status_closed": {"zh-CN": "休市", "ja": "休場", "en": "Closed", "th": "ปิดตลาด"},
    "status_pre": {"zh-CN": "盘前", "ja": "プレ", "en": "Pre-market", "th": "ก่อนเปิด"},
    "status_open": {"zh-CN": "盘中", "ja": "取引中", "en": "Open", "th": "เปิดตลาด"},
    "status_post": {"zh-CN": "盘后", "ja": "アフター", "en": "Post-market", "th": "หลังปิด"},
}

query_lang = st.query_params.get("lang", "zh-CN")
if query_lang not in LANGS:
    query_lang = "zh-CN"
if "lang" not in st.session_state:
    st.session_state.lang = query_lang


def tr(key: str) -> str:
    return I18N.get(key, {}).get(st.session_state.lang, key)


def sentiment_key(value: str) -> str:
    mapping = {"利好": "bullish", "中性": "neutral", "利空": "bearish"}
    return mapping.get(value, "neutral")


def tr_sentiment(value: str) -> str:
    return tr(sentiment_key(value))


st.set_page_config(page_title="Stock Dashboard", layout="wide")
selected_lang = st.selectbox(
    tr("language"),
    options=list(LANGS.keys()),
    index=list(LANGS.keys()).index(st.session_state.lang),
    format_func=lambda code: LANGS[code],
)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
if st.query_params.get("lang") != st.session_state.lang:
    st.query_params["lang"] = st.session_state.lang
st.title(tr("app_title"))
st.caption(tr("app_caption"))


def _to_datetime_safe(value: str) -> datetime | None:
    if not value:
        return None
    fmts = ["%Y-%m-%d %H:%M", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"]
    for fmt in fmts:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return None


def compute_news_impact(price_df: pd.DataFrame, event_time: datetime) -> dict[str, float | None]:
    if price_df.empty or event_time is None:
        return {"base": None, "1h": None, "4h": None, "1d": None}

    series = price_df["Close"].copy()
    series.index = pd.to_datetime(series.index).tz_localize(None)

    nearest_idx = series.index.get_indexer([event_time], method="nearest")[0]
    base_price = float(series.iloc[nearest_idx])
    base_time = series.index[nearest_idx]

    def forward_change(delta: timedelta) -> float | None:
        target = base_time + delta
        later = series[series.index >= target]
        if later.empty or base_price == 0:
            return None
        return float((later.iloc[0] / base_price - 1.0) * 100.0)

    return {
        "base": base_price,
        "1h": forward_change(timedelta(hours=1)),
        "4h": forward_change(timedelta(hours=4)),
        "1d": forward_change(timedelta(days=1)),
    }


def estimate_capital_flow(df: pd.DataFrame, threshold_quantile: float = 0.7) -> tuple[pd.DataFrame, dict]:
    flow = df.copy()
    flow["price_diff"] = flow["Close"].diff().fillna(0.0)
    flow["direction"] = flow["price_diff"].apply(lambda x: 1 if x >= 0 else -1)
    flow["Amount"] = flow["Amount"].fillna(0.0)

    threshold = float(flow["Amount"].quantile(threshold_quantile)) if not flow.empty else 0.0
    flow["is_main"] = flow["Amount"] >= threshold
    flow["main_amount"] = flow.apply(lambda r: r["Amount"] if r["is_main"] else 0.0, axis=1)
    flow["retail_amount"] = flow.apply(lambda r: r["Amount"] if not r["is_main"] else 0.0, axis=1)

    flow["main_net"] = flow["main_amount"] * flow["direction"]
    flow["retail_net"] = flow["retail_amount"] * flow["direction"]

    summary = {
        "total_amount": float(flow["Amount"].sum()),
        "main_net": float(flow["main_net"].sum()),
        "retail_net": float(flow["retail_net"].sum()),
        "main_share": float(flow["main_amount"].sum() / flow["Amount"].sum()) if flow["Amount"].sum() else 0.0,
        "threshold_amount": threshold,
    }
    return flow, summary


def get_realtime_intraday(symbol: str) -> tuple[dict, pd.DataFrame, dict]:
    stock_code = symbol.split(".")[0]
    to_date = datetime.today().strftime("%d/%m/%Y")
    from_date = (datetime.today() - timedelta(days=10)).strftime("%d/%m/%Y")

    source = "Investing.com"
    try:
        # investpy does not always expose stable 1-minute ticks for all symbols.
        # We use recent data from Investing.com and render the latest segment.
        intraday = investpy.get_stock_historical_data(
            stock=stock_code,
            country="hong kong",
            from_date=from_date,
            to_date=to_date,
        ).reset_index()
        if intraday.empty:
            raise ValueError("empty investpy result")

        intraday = intraday.rename(columns={"Date": "Datetime"}).dropna(subset=["Close", "Volume"]).copy()
        intraday = intraday.tail(30)
        intraday = intraday.set_index("Datetime")
    except Exception:
        source = "Yahoo Finance (fallback)"
        ticker = yf.Ticker(symbol)
        intraday = ticker.history(period="1d", interval="1m").dropna(subset=["Close", "Volume"]).copy()
        if intraday.empty:
            raise ValueError(tr("err_no_realtime_data"))

    intraday["Amount"] = intraday["Close"] * intraday["Volume"]
    flow_df, flow_summary = estimate_capital_flow(intraday)
    last_price = float(intraday["Close"].iloc[-1])
    prev_price = float(intraday["Close"].iloc[-2]) if len(intraday) > 1 else last_price
    delta = last_price - prev_price
    pct = (delta / prev_price * 100) if prev_price else 0.0

    snapshot = {
        "price": last_price,
        "delta": delta,
        "pct": pct,
        "latest_amount": float(intraday["Amount"].iloc[-1]),
        "source": source,
    }
    return snapshot, flow_df, flow_summary


def get_realtime_quote(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d", interval="1m").dropna(subset=["Close"]).copy()
    if hist.empty:
        raise ValueError(tr("err_no_quote"))

    latest = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else latest
    day_high = float(hist["High"].max()) if "High" in hist.columns else latest
    day_low = float(hist["Low"].min()) if "Low" in hist.columns else latest
    day_open = float(hist["Open"].iloc[0]) if "Open" in hist.columns else latest

    # Approximate previous close using previous day close if possible.
    daily = ticker.history(period="5d", interval="1d").dropna(subset=["Close"]).copy()
    prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else prev

    delta = latest - prev_close
    pct = (delta / prev_close * 100) if prev_close else 0.0

    return {
        "price": latest,
        "delta": delta,
        "pct": pct,
        "open": day_open,
        "high": day_high,
        "low": day_low,
        "prev_close": prev_close,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Yahoo Finance (realtime quote)",
    }


def get_us_session_quotes(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="2d", interval="1m", prepost=True).dropna(subset=["Close"]).copy()
    if df.empty:
        raise ValueError(tr("err_no_us_session"))

    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df_local = df.tz_convert("US/Eastern")
    today = pd.Timestamp.now(tz="US/Eastern").date()
    today_df = df_local[df_local.index.date == today].copy()
    if today_df.empty:
        today_df = df_local.tail(500).copy()

    regular = today_df.between_time("09:30", "16:00")
    pre = today_df.between_time("04:00", "09:29")
    post = today_df.between_time("16:01", "20:00")

    daily = ticker.history(period="5d", interval="1d").dropna(subset=["Close"]).copy()
    prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else float(today_df["Close"].iloc[-1])
    last_price = float(today_df["Close"].iloc[-1])
    delta = last_price - prev_close
    pct = (delta / prev_close * 100) if prev_close else 0.0

    pre_price = float(pre["Close"].iloc[-1]) if not pre.empty else None
    post_price = float(post["Close"].iloc[-1]) if not post.empty else None
    regular_price = float(regular["Close"].iloc[-1]) if not regular.empty else None

    return {
        "last_price": last_price,
        "delta": delta,
        "pct": pct,
        "prev_close": prev_close,
        "regular_price": regular_price,
        "pre_price": pre_price,
        "post_price": post_price,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_us_kline(symbol: str, interval: str, include_extended: bool) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)

    if interval == "3m":
        base = ticker.history(period="7d", interval="1m", prepost=include_extended).dropna(
            subset=["Open", "High", "Low", "Close"]
        )
        if base.empty:
            raise ValueError(tr("err_no_3m_base"))
        if base.index.tz is None:
            base.index = base.index.tz_localize("UTC")
        base = base.tz_convert("US/Eastern")
        resampled = pd.DataFrame()
        resampled["Open"] = base["Open"].resample("3min").first()
        resampled["High"] = base["High"].resample("3min").max()
        resampled["Low"] = base["Low"].resample("3min").min()
        resampled["Close"] = base["Close"].resample("3min").last()
        resampled["Volume"] = base["Volume"].resample("3min").sum()
        resampled = resampled.dropna(subset=["Open", "High", "Low", "Close"]).tail(400)
        return resampled

    period_map = {
        "1m": "7d",
        "15m": "60d",
        "30m": "60d",
        "60m": "730d",
        "1d": "5y",
    }
    raw = ticker.history(period=period_map[interval], interval=interval, prepost=include_extended).dropna(
        subset=["Open", "High", "Low", "Close"]
    )
    if raw.empty:
        raise ValueError(tr("err_no_kline").format(interval=interval))
    if raw.index.tz is None:
        raw.index = raw.index.tz_localize("UTC")
    return raw.tz_convert("US/Eastern").tail(400)


def get_us_market_status() -> dict:
    now_et = pd.Timestamp.now(tz="US/Eastern")
    t = now_et.time()
    weekday = now_et.weekday()

    if weekday >= 5:
        return {"label": tr("status_closed"), "color": "gray", "time": now_et.strftime("%Y-%m-%d %H:%M:%S")}
    if t >= datetime.strptime("04:00", "%H:%M").time() and t < datetime.strptime("09:30", "%H:%M").time():
        return {"label": tr("status_pre"), "color": "orange", "time": now_et.strftime("%Y-%m-%d %H:%M:%S")}
    if t >= datetime.strptime("09:30", "%H:%M").time() and t <= datetime.strptime("16:00", "%H:%M").time():
        return {"label": tr("status_open"), "color": "green", "time": now_et.strftime("%Y-%m-%d %H:%M:%S")}
    if t > datetime.strptime("16:00", "%H:%M").time() and t <= datetime.strptime("20:00", "%H:%M").time():
        return {"label": tr("status_post"), "color": "blue", "time": now_et.strftime("%Y-%m-%d %H:%M:%S")}
    return {"label": tr("status_closed"), "color": "gray", "time": now_et.strftime("%Y-%m-%d %H:%M:%S")}

with st.sidebar:
    st.header(tr("sidebar_header"))
    market = st.selectbox(
        tr("market"),
        options=["hk", "us"],
        index=0,
        format_func=lambda m: tr("market_hk") if m == "hk" else tr("market_us"),
    )
    default_symbol = "0020.HK" if market == "hk" else "TSLA"
    symbol = st.text_input(tr("stock_code"), value=default_symbol)
    lookback_days = st.slider(tr("history_days"), min_value=20, max_value=120, value=30, step=5)
    threshold_pct = st.slider(tr("threshold_pct"), min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    fund_quantile = st.slider(tr("fund_quantile"), min_value=0.5, max_value=0.95, value=0.7, step=0.05)
    news_keywords = st.text_input(tr("news_keywords"), value="商汤 OR SenseTime OR 0020.HK OR AI")
    us_kline_interval = st.selectbox(
        tr("us_kline_interval"),
        options=["1m", "3m", "15m", "30m", "60m", "1d"],
        index=0,
        format_func=lambda x: tr(f"interval_{x}"),
    )
    us_include_extended = st.checkbox(tr("include_ext"), value=True)
    us_auto_refresh = st.checkbox(tr("auto_refresh"), value=False)
    us_refresh_seconds = st.slider(tr("auto_refresh_sec"), min_value=5, max_value=60, value=15, step=5)
    run_btn = st.button(tr("run_history"), type="primary")
    refresh_realtime = st.button(tr("refresh_realtime"))
    refresh_quote = st.button(tr("refresh_quote"))
    refresh_us = st.button(tr("refresh_us"))
    refresh_news = st.button(tr("refresh_news"))

tab_quote, tab_realtime, tab_us, tab_news, tab_history = st.tabs(
    [tr("tab_quote"), tr("tab_realtime"), tr("tab_us"), tr("tab_news"), tr("tab_history")]
)

with tab_history:
    if run_btn:
        try:
            df, summary = run_pipeline(
                symbol=symbol.strip(),
                lookback_days=lookback_days,
                threshold=threshold_pct / 100.0,
            )

            st.success(tr("pipeline_success"))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(tr("latest_close"), f"{summary['latest_close']:.3f}")
            c2.metric(tr("avg_return"), f"{summary['avg_daily_return'] * 100:.2f}%")
            c3.metric(tr("max_return"), f"{summary['max_daily_return'] * 100:.2f}%")
            c4.metric(tr("rise_ratio").format(pct=f"{threshold_pct:.1f}"), f"{summary['up_days_ratio'] * 100:.2f}%")

            fig, (ax1, ax2) = plt.subplots(
                nrows=2,
                ncols=1,
                figsize=(12, 8),
                gridspec_kw={"height_ratios": [2, 1]},
                sharex=True,
            )

            date_series = pd.to_datetime(df["Date"])
            ax1.plot(date_series, df["Close"], label="Close", linewidth=2)
            ax1.plot(date_series, df["SMA"], label="SMA(5)", linewidth=1.8)
            ax1.plot(date_series, df["EMA"], label="EMA(12)", linewidth=1.8)
            ax1.set_title(f"{symbol} {tr('close_ma')}")
            ax1.set_ylabel("Price")
            ax1.grid(alpha=0.25)
            ax1.legend()

            amount_series = df["Close"] * df["Volume"]
            amount_trend = amount_series.ewm(span=5, adjust=False).mean()
            ax2.plot(date_series, amount_series, linewidth=1.0, color="#fbbf24", alpha=0.35, label="Raw Amount")
            ax2.plot(date_series, amount_trend, linewidth=2.2, color="#f59e0b", label="EMA Trend")
            ax2.set_title(tr("amount_trend"))
            ax2.set_ylabel("Amount")
            ax2.grid(alpha=0.25)
            ax2.legend()

            plt.xticks(rotation=30)
            plt.tight_layout()
            st.pyplot(fig)

            st.subheader(tr("key_report"))
            st.write(
                f"{tr('report_line1').format(days=lookback_days, avg=summary['avg_daily_return'] * 100)}  \n"
                f"{tr('report_line2').format(maxv=summary['max_daily_return'] * 100)}  \n"
                f"{tr('report_line3').format(pct=threshold_pct, ratio=summary['up_days_ratio'] * 100)}"
            )

            st.subheader(tr("details_data"))
            st.dataframe(df, use_container_width=True)

            st.info(cron_integration_note())
            st.caption(tr("persist_caption"))
        except Exception as exc:
            st.error(tr("run_failed").format(err=exc))
    else:
        st.write(tr("click_run_tip"))

with tab_realtime:
    st.subheader(tr("realtime_subheader"))
    st.caption(tr("realtime_caption"))
    if refresh_realtime:
        st.cache_data.clear()

    @st.cache_data(ttl=8)
    def load_realtime(symbol_input: str) -> tuple[dict, pd.DataFrame, dict]:
        return get_realtime_intraday(symbol_input)

    try:
        snapshot, intraday_df, flow_summary = load_realtime(symbol.strip())
        if "Amount" in intraday_df.columns and ("main_amount" not in intraday_df.columns):
            intraday_df, flow_summary = estimate_capital_flow(intraday_df, threshold_quantile=fund_quantile)
        elif "main_amount" in intraday_df.columns:
            intraday_df, flow_summary = estimate_capital_flow(intraday_df, threshold_quantile=fund_quantile)

        r1, r2, r3, r4 = st.columns(4)
        r1.metric(tr("latest_price"), f"{snapshot['price']:.3f}", delta=f"{snapshot['delta']:.3f}")
        r2.metric(tr("chg_pct"), f"{snapshot['pct']:.2f}%")
        r3.metric(tr("latest_1m_amount"), f"{snapshot['latest_amount']:,.2f}")
        r4.metric(tr("main_share"), f"{flow_summary['main_share'] * 100:.2f}%")
        st.caption(tr("current_source").format(src=snapshot["source"]))

        chart_df = intraday_df.copy()
        chart_df.index = chart_df.index.tz_localize(None)
        st.line_chart(chart_df["Close"], height=260)
        amount_display = pd.DataFrame(index=chart_df.index)
        amount_display["Raw Amount"] = chart_df["Amount"]
        amount_display["EMA Trend"] = chart_df["Amount"].ewm(span=6, adjust=False).mean()
        st.line_chart(amount_display, height=220)

        flow_trend_fig = go.Figure()
        flow_trend_fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["main_amount"],
                mode="lines",
                name=tr("main_flow"),
                line=dict(color="red", width=2.2),
            )
        )
        flow_trend_fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["retail_amount"],
                mode="lines",
                name=tr("retail_flow"),
                line=dict(color="white", width=2.0),
            )
        )
        flow_trend_fig.update_layout(
            height=260,
            title=tr("flow_trend"),
            xaxis_title=tr("time_axis"),
            yaxis_title=tr("flow_scale"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=45, b=20),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="#e2e8f0"),
        )
        st.plotly_chart(flow_trend_fig, use_container_width=True)
        st.bar_chart(chart_df["main_net"], height=200)

        f1, f2, f3 = st.columns(3)
        f1.metric(tr("total_amount"), f"{flow_summary['total_amount']:,.2f}")
        f2.metric(tr("main_net"), f"{flow_summary['main_net']:,.2f}")
        f3.metric(tr("retail_net"), f"{flow_summary['retail_net']:,.2f}")
        st.caption(tr("chart_order"))
        st.caption(tr("main_threshold").format(q=fund_quantile, v=flow_summary["threshold_amount"]))
        st.warning(tr("flow_warning"))
    except Exception as exc:
        st.error(tr("realtime_failed").format(err=exc))

with tab_quote:
    st.subheader(tr("quote_subheader"))
    st.caption(tr("quote_caption"))
    if refresh_quote:
        st.cache_data.clear()

    @st.cache_data(ttl=5)
    def load_quote(symbol_input: str) -> dict:
        return get_realtime_quote(symbol_input)

    try:
        quote = load_quote(symbol.strip())
        q1, q2, q3, q4 = st.columns(4)
        q1.metric(tr("latest_price"), f"{quote['price']:.3f}", delta=f"{quote['delta']:.3f}")
        q2.metric(tr("chg_pct"), f"{quote['pct']:.2f}%")
        q3.metric(tr("day_high"), f"{quote['high']:.3f}")
        q4.metric(tr("day_low"), f"{quote['low']:.3f}")

        q5, q6 = st.columns(2)
        q5.metric(tr("day_open"), f"{quote['open']:.3f}")
        q6.metric(tr("prev_close"), f"{quote['prev_close']:.3f}")
        st.caption(tr("quote_source_time").format(src=quote["source"], t=quote["updated_at"]))
    except Exception as exc:
        st.error(tr("quote_failed").format(err=exc))

with tab_us:
    st.subheader(tr("us_subheader"))
    st.caption(tr("us_caption"))
    if market != "us":
        st.info(tr("switch_market_us"))
    else:
        if us_auto_refresh:
            st_autorefresh(interval=us_refresh_seconds * 1000, key="us_kline_autorefresh")

        if refresh_us:
            st.cache_data.clear()

        @st.cache_data(ttl=8)
        def load_us_quote(symbol_input: str) -> dict:
            return get_us_session_quotes(symbol_input)

        @st.cache_data(ttl=12)
        def load_us_kline(symbol_input: str, interval_label: str, include_extended: bool) -> pd.DataFrame:
            return get_us_kline(symbol_input, interval_label, include_extended)

        try:
            market_status = get_us_market_status()
            st.markdown(
                f"**{tr('session_status')}：** :{market_status['color']}[{market_status['label']}]  "
                f"({tr('time_et')} {market_status['time']})"
            )

            us_quote = load_us_quote(symbol.strip().upper())
            u1, u2, u3, u4 = st.columns(4)
            u1.metric(tr("latest_price"), f"{us_quote['last_price']:.3f}", delta=f"{us_quote['delta']:.3f}")
            u2.metric(tr("chg_pct"), f"{us_quote['pct']:.2f}%")
            u3.metric(tr("pre_market"), f"{us_quote['pre_price']:.3f}" if us_quote["pre_price"] is not None else "N/A")
            u4.metric(tr("after_market"), f"{us_quote['post_price']:.3f}" if us_quote["post_price"] is not None else "N/A")
            st.caption(tr("update_et").format(p=us_quote["prev_close"], t=us_quote["updated_at"]))

            kline_df = load_us_kline(symbol.strip().upper(), us_kline_interval, us_include_extended)
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=kline_df.index,
                        open=kline_df["Open"],
                        high=kline_df["High"],
                        low=kline_df["Low"],
                        close=kline_df["Close"],
                        increasing_line_color="#22c55e",
                        decreasing_line_color="#ef4444",
                        name=tr("kline"),
                    )
                ]
            )
            fig.update_layout(
                height=480,
                title=tr("rt_kline_title").format(sym=symbol.strip().upper(), iv=tr(f"interval_{us_kline_interval}")),
                xaxis_title=f"{tr('time_axis')} (US/Eastern)",
                yaxis_title=tr("price_axis"),
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(tr("us_failed").format(err=exc))

with tab_news:
    st.subheader(tr("news_subheader"))
    st.caption(tr("news_caption"))
    if refresh_news:
        st.cache_data.clear()

    @st.cache_data(ttl=300)
    def load_news(keyword_query: str) -> list[dict]:
        return fetch_news(keyword_query, limit=15)

    try:
        news_items = load_news(news_keywords.strip())
        if not news_items:
            st.info(tr("no_news"))
        else:
            sentiment_counts = pd.Series([item["sentiment"] for item in news_items]).value_counts()
            n1, n2, n3 = st.columns(3)
            n1.metric(tr("bullish"), int(sentiment_counts.get("利好", 0)))
            n2.metric(tr("neutral"), int(sentiment_counts.get("中性", 0)))
            n3.metric(tr("bearish"), int(sentiment_counts.get("利空", 0)))

            available_sources = sorted({(item.get("source") or tr("unknown_source")) for item in news_items})
            source_filter = st.selectbox(tr("source_filter"), [tr("all")] + available_sources, index=0)
            sentiment_filter = st.selectbox(tr("sentiment_filter"), ["all", "利好", "中性", "利空"], index=0, format_func=lambda s: tr("all") if s == "all" else tr_sentiment(s))
            filtered_news = news_items
            if source_filter != tr("all"):
                filtered_news = [item for item in filtered_news if (item.get("source") or tr("unknown_source")) == source_filter]
            if sentiment_filter != "all":
                filtered_news = [item for item in filtered_news if item["sentiment"] == sentiment_filter]
            if not filtered_news:
                st.info(tr("no_news_filtered"))
            else:
                news_options = [
                    f"{i + 1}. {item['published_at']} | {tr_sentiment(item['sentiment'])} | {item['title'][:60]}"
                    for i, item in enumerate(filtered_news)
                ]
                selected_option = st.selectbox(tr("select_news"), news_options, index=0)
                selected_idx = news_options.index(selected_option)
                selected_news = filtered_news[selected_idx]

                st.markdown(
                    f"**{tr('current_event')}：** [{selected_news['title']}]({selected_news['url']})  \n"
                    f"{tr('source')}：{selected_news['source'] or tr('unknown_source')} | "
                    f"{tr('time')}：{selected_news['published_at']} | "
                    f"{tr('sentiment')}：**{tr_sentiment(selected_news['sentiment'])}**"
                )

                @st.cache_data(ttl=12)
                def load_price_for_news(symbol_input: str) -> pd.DataFrame:
                    _, intraday, _ = get_realtime_intraday(symbol_input)
                    return intraday

                price_df = load_price_for_news(symbol.strip())
                chart_df = price_df.copy()
                chart_df.index = pd.to_datetime(chart_df.index).tz_localize(None)

                event_dt = _to_datetime_safe(selected_news["published_at"])
                if event_dt is not None:
                    event_ts = pd.to_datetime(event_dt)
                    nearest_pos = chart_df.index.get_indexer([event_ts], method="nearest")[0]
                    nearest_time = chart_df.index[nearest_pos]

                    fig, ax = plt.subplots(figsize=(10, 3.5))
                    ax.plot(chart_df.index, chart_df["Close"], linewidth=1.8, label="Close")
                    ax.axvline(nearest_time, color="red", linestyle="--", linewidth=1.2, label=tr("news_event"))
                    ax.scatter([nearest_time], [chart_df["Close"].iloc[nearest_pos]], color="red", s=24)
                    ax.set_title(tr("event_price_link"))
                    ax.grid(alpha=0.25)
                    ax.legend()
                    plt.xticks(rotation=30)
                    plt.tight_layout()
                    st.pyplot(fig)

                    impact = compute_news_impact(chart_df, event_dt)
                    i1, i2, i3, i4 = st.columns(4)
                    i1.metric(tr("event_base"), f"{impact['base']:.3f}" if impact["base"] is not None else "N/A")
                    i2.metric(tr("after_1h"), f"{impact['1h']:.2f}%" if impact["1h"] is not None else "N/A")
                    i3.metric(tr("after_4h"), f"{impact['4h']:.2f}%" if impact["4h"] is not None else "N/A")
                    i4.metric(tr("after_1d"), f"{impact['1d']:.2f}%" if impact["1d"] is not None else "N/A")

                st.markdown("---")
                for item in filtered_news:
                    st.markdown(
                        f"- [{item['title']}]({item['url']})  \n"
                        f"  {tr('source')}：{item['source'] or tr('unknown_source')} | "
                        f"{tr('time')}：{item['published_at']} | "
                        f"{tr('sentiment')}：**{tr_sentiment(item['sentiment'])}**"
                    )
            st.caption(tr("news_capture_time").format(t=news_items[0]["captured_at"]))
    except Exception as exc:
        st.error(tr("news_failed").format(err=exc))
