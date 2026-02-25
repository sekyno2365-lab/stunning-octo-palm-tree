from flask import Flask, render_template_string, request
import requests

app = Flask(__name__)

# --- 設定（あなたのID） ---
DMM_AFFILIATE_ID = "SeK2365-990"
DMM_API_ID = "SK9rMSVHgnTRk5CvtkhW"

def get_fanza_items(keyword=None, page=1, floor='videoa'):
    url = "https://api.dmm.com/affiliate/v3/ItemList"
    hits = 100
    offset = ((page - 1) * hits) + 1
    
    params = {
        "api_id": DMM_API_ID,
        "affiliate_id": DMM_AFFILIATE_ID,
        "site": "FANZA",
        "service": "digital",
        "floor": floor,
        "hits": hits,
        "offset": offset,
        "sort": "rank",
        "output": "json"
    }
    if keyword:
        params["keyword"] = keyword
        
    try:
        r = requests.get(url, params=params)
        data = r.json().get('result', {})
        items = data.get('items', [])
        total_count = int(data.get('total_count', 0))
        return items, total_count
    except:
        return [], 0

@app.route('/')
def home():
    query = request.args.get('q', '')
    floor = request.args.get('floor', 'videoa')
    try:
        page = int(request.args.get('page', 1))
    except:
        page = 1
        
    items, total_count = get_fanza_items(keyword=query, page=page, floor=floor)
    
    for item in items:
        # --- 画像取得ロジックの強化 ---
        img_url = ""
        image_data = item.get('imageURL', {})
        if image_data:
            img_url = image_data.get('large') or image_data.get('small') or ""
        
        if not img_url and 'sampleImageURL' in item:
            sample_data = item.get('sampleImageURL', {}).get('sample_s', {})
            if sample_data:
                images = sample_data.get('image', [])
                img_url = images[0] if isinstance(images, list) and images else images

        item['display_img'] = img_url

        # 金額計算
        max_price = 0
        try:
            deliveries = item.get('prices', {}).get('deliveries', {}).get('delivery', [])
            if isinstance(deliveries, list):
                prices = [int(d['price']) for d in deliveries if 'price' in d]
                if prices: max_price = max(prices)
            elif isinstance(deliveries, dict):
                max_price = int(deliveries.get('price', 0))
        except:
            max_price = 0
        item['display_price'] = f"{max_price:,}" if max_price > 0 else "---"

    html_template = """
    <!DOCTYPE html>
    <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>最新無料FANZAカタログ</title>
            <style>
                body { 
                    font-family: "Helvetica Neue", Arial, sans-serif; 
                    background: #f0f2f5; 
                    margin: 0; padding: 0; color: #333; 
                }
                header {
                    background: linear-gradient(135deg, #444 0%, #111 100%);
                    color: #fff; padding: 20px 0 10px 0; text-align: center;
                    position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .logo-link { text-decoration: none; color: inherit; }
                header h1 { margin: 0 0 15px 0; font-size: 1.4em; letter-spacing: 2px; font-weight: 800; }
                
                .floor-tabs { display: flex; justify-content: center; gap: 8px; margin: 15px 0; flex-wrap: wrap; padding: 0 10px; }
                .tab-btn {
                    padding: 8px 16px; background: rgba(255,255,255,0.1); color: #fff;
                    text-decoration: none; border-radius: 20px; font-size: 0.85em; border: 1px solid rgba(255,255,255,0.3); transition: 0.3s;
                }
                .tab-btn.active { background: #28a745; border-color: #28a745; font-weight: bold; }

                .search-box form { display: flex; justify-content: center; margin-bottom: 10px; }
                .search-box input { padding: 10px 15px; width: 60%; max-width: 300px; border-radius: 25px 0 0 25px; border: none; outline: none; }
                .search-box button { padding: 10px 20px; border-radius: 0 25px 25px 0; border: none; background: #28a745; color: white; cursor: pointer; font-weight: bold; }

                .main-content { padding: 20px 10px; text-align: center; }
                .container { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; text-align: left; }
                .item-card { background: #fff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; display: flex; flex-direction: column; transition: 0.2s; }
                .item-card:hover { transform: translateY(-3px); }
                .img-box { width: 100%; aspect-ratio: 1 / 1.4; overflow: hidden; background: #000; display: flex; align-items: center; justify-content: center; }
                img { width: 100%; height: 100%; object-fit: contain; }
                .info { padding: 12px; flex-grow: 1; display: flex; flex-direction: column; }
                .title { font-size: 0.85em; font-weight: bold; height: 3em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 10px; line-height: 1.4; }
                .price { color: #e53935; font-weight: bold; margin-bottom: 12px; }
                .btn { display: block; background: #28a745; color: #fff; padding: 10px; text-decoration: none; border-radius: 6px; text-align: center; font-size: 0.8em; font-weight: bold; margin-top: auto; }

                .pagination { margin: 40px 0; display: flex; justify-content: center; align-items: center; gap: 15px; }
                .page-btn { padding: 10px 20px; background: #fff; border: 1px solid #ddd; text-decoration: none; color: #333; border-radius: 25px; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <header>
                <a href="/" class="logo-link"><h1>最新無料FANZAカタログ</h1></a>
                <div class="search-box">
                    <form action="/" method="get">
                        <input type="hidden" name="floor" value="{{ floor }}">
                        <input type="text" name="q" placeholder="キーワード検索..." value="{{ query }}">
                        <button type="submit">検索</button>
                    </form>
                </div>
                <div class="floor-tabs">
                    <a href="/?floor=videoa&q={{ query }}" class="tab-btn {{ 'active' if floor == 'videoa' }}">🎥 ビデオ</a>
                    <a href="/?floor=videoc&q={{ query }}" class="tab-btn {{ 'active' if floor == 'videoc' }}">🔞 素人</a>
                    <a href="/?floor=anime&q={{ query }}" class="tab-btn {{ 'active' if floor == 'anime' }}">🎨 アニメ</a>
                </div>
            </header>

            <div class="main-content">
                <p style="margin-bottom:20px;">
                    現在のジャンル: <strong>
                        {% if floor == 'videoa' %}ビデオ{% elif floor == 'videoc' %}素人{% elif floor == 'anime' %}アニメ{% endif %}
                    </strong> 
                    {% if query %}/ 「{{ query }}」の検索結果{% endif %} : {{ total_count }}件
                </p>
                <div class="container">
                    {% for item in items %}
                    <div class="item-card">
                        <div class="img-box">
                            {% if item.display_img %}<img src="{{ item.display_img }}" referrerpolicy="no-referrer">{% else %}<div style="color:#666; font-size:0.7em;">画像準備中</div>{% endif %}
                        </div>
                        <div class="info">
                            <div class="title">{{ item.title }}</div>
                            <div class="price">価格:{{ item.display_price }}円</div>
                            <a href="{{ item.affiliateURL }}" class="btn" target="_blank">無料サンプルを見る</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="pagination">
                    {% if page > 1 %}<a href="/?q={{ query }}&floor={{ floor }}&page={{ page - 1 }}" class="page-btn">← 前へ</a>{% endif %}
                    <span class="current-page">{{ page }}</span>
                    {% if page * 100 < total_count %}<a href="/?q={{ query }}&floor={{ floor }}&page={{ page + 1 }}" class="page-btn">次へ →</a>{% endif %}
                </div>
            </div>
        </body>
    </html>
    """
    return render_template_string(html_template, items=items, query=query, page=page, total_count=total_count, floor=floor)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

