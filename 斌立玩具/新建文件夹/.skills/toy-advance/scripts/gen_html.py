import csv, os, sys
from collections import defaultdict

def find_cols(headers):
    qty_col = amount_col = status_col = None
    for i, h in enumerate(headers):
        h = h.strip()
        if "商品数量" in h: qty_col = i
        elif "商品金额" in h: amount_col = i
        elif h == "订单状态": status_col = i
    if None in (qty_col, amount_col, status_col):
        print("Error: missing cols"); sys.exit(1)
    return qty_col, amount_col, status_col

def gen_html(base_dir, output_dir):
    accounts = [
        ("麦6", "麦6-4-5月", "店6"),
        ("麦7", "麦7-4-5月", "店7"),
        ("麦8", "麦8-4-5月", "店8"),
    ]
    months_data = {}
    for aname, adir, slabel in accounts:
        fdir = os.path.join(base_dir, adir)
        ofile = os.path.join(fdir, "订单.csv")
        mgross = defaultdict(float); mclosed = defaultdict(float)
        with open(ofile, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f); headers = next(reader)
            qc, ac, sc = find_cols(headers)
            dc = None
            for i, h in enumerate(headers):
                if "提交" in h or "下单" in h: dc = i; break
            for row in reader:
                try:
                    qty = int(row[qc]) if row[qc] else 0
                    amt = float(row[ac]) if row[ac] else 0.0
                    st = row[sc].strip(); line = qty * amt
                    m = row[dc].strip()[:7] if dc is not None and row[dc] else "2026-04"
                    mgross[m] += line
                    if st == "已关闭": mclosed[m] += line
                except: continue

        settle = defaultdict(float)
        for fname in os.listdir(fdir):
            if "结算" in fname and fname.endswith(".csv"):
                m = "2026-04" if "4月" in fname else ("2026-05" if "5月" in fname else None)
                if not m: continue
                fp = os.path.join(fdir, fname); es = 0.0
                with open(fp, "r", encoding="utf-8-sig") as sf:
                    rdr = csv.reader(sf); next(rdr); next(rdr)
                    for row in rdr:
                        try:
                            if len(row) > 40 and row[40]: es += float(row[40])
                        except: pass
                settle[m] += abs(es)

        dynfile = None
        for fname in os.listdir(fdir):
            if "动账" in fname and fname.endswith(".csv"): dynfile = os.path.join(fdir, fname); break
        mdyn = defaultdict(float); mdep = defaultdict(float)
        if dynfile:
            with open(dynfile, "r", encoding="utf-8-sig") as f:
                rdr = csv.reader(f); next(rdr)
                for row in rdr:
                    if not row[0] or not row[0].strip(): continue
                    if row[2].strip() != "出账": continue
                    try: amt = float(row[3])
                    except: continue
                    m = row[0].strip()[:7]
                    scn = row[5].strip() if len(row) > 5 else ""
                    rmk = row[38].strip() if len(row) > 38 and row[38] else ""
                    is_dep = ("保证金" in scn or "保证金" in rmk)
                    if is_dep and abs(amt) >= 100: mdep[m] += abs(amt)
                    else: mdyn[m] += abs(amt)

        for m in sorted(set(list(mgross.keys()) + list(settle.keys()) + list(mdyn.keys()))):
            if m not in months_data: months_data[m] = {}
            months_data[m][aname] = {
                "gross": round(mgross.get(m, 0), 2),
                "closed": round(mclosed.get(m, 0), 2),
                "plat": round(settle.get(m, 0), 2),
                "dyn": round(mdyn.get(m, 0), 2),
                "dep": round(mdep.get(m, 0), 2),
            }

    acct_order = ["麦6", "麦7", "麦8"]
    def fm(n): return "{:,.2f}".format(n)

    rows = ""
    for m in sorted(months_data.keys()):
        cls = "row-apr" if "04" in m else "row-may"
        label = m + " 汇总"
        data = months_data[m]
        g = [data.get(a, {}).get("gross", 0) for a in acct_order]
        c = [data.get(a, {}).get("closed", 0) for a in acct_order]
        a_sales = [round(g[i] - c[i], 2) for i in range(3)]
        dyn = [data.get(a, {}).get("dyn", 0) for a in acct_order]
        plat = [data.get(a, {}).get("plat", 0) for a in acct_order]

        tg = sum(g); tc = sum(c); ta = round(tg - tc, 2)
        tdyn = round(sum(dyn), 2); tplat = round(sum(plat), 2)
        advance = round(ta * 0.9, 2)
        reserve = round(ta * 0.1, 2)
        service_fee = round(ta * 0.05, 2)
        tax = round(ta * 0.02, 2)
        paid_diff = round(advance - tdyn, 2)
        remaining = round(reserve - service_fee - tax - tplat - tdyn, 2)

        vals = [fm(v) for v in g]
        vals += [fm(v) for v in dyn]
        vals += [fm(v) for v in a_sales]
        vals += [fm(advance), fm(advance), fm(reserve), fm(service_fee), fm(tplat), fm(tdyn), fm(paid_diff), fm(tax)]
        cls_r = "negative" if remaining < 0 else ""
        vals += [fm(remaining)]

        tds = '<td class="label">' + label + '</td>'
        for vi, v in enumerate(vals):
            ec = cls_r if vi == len(vals) - 1 else ""
            tds += '<td class="' + ec + '">' + v + '</td>'
        tds += '<td></td>'
        rows += '<tr class="' + cls + '">' + tds + '</tr>\n'

    # Grand total
    g_all = []
    for i in range(3):
        a = acct_order[i]
        gg = sum(months_data[m].get(a, {}).get("gross", 0) for m in months_data)
        g_all.append(round(gg, 2))
    c_all = []
    for i in range(3):
        a = acct_order[i]
        cc = sum(months_data[m].get(a, {}).get("closed", 0) for m in months_data)
        c_all.append(round(cc, 2))
    a_all = [round(g_all[i] - c_all[i], 2) for i in range(3)]
    dyn_all = []
    for i in range(3):
        a = acct_order[i]
        dd = sum(months_data[m].get(a, {}).get("dyn", 0) for m in months_data)
        dyn_all.append(round(dd, 2))
    plat_all = []
    for i in range(3):
        a = acct_order[i]
        pp = sum(months_data[m].get(a, {}).get("plat", 0) for m in months_data)
        plat_all.append(round(pp, 2))

    tg_all = round(sum(g_all), 2); tc_all = round(sum(c_all), 2); ta_all = round(tg_all - tc_all, 2)
    tdyn_all = round(sum(dyn_all), 2); tplat_all = round(sum(plat_all), 2)
    adv_all = round(ta_all * 0.9, 2); res_all = round(ta_all * 0.1, 2)
    srv_all = round(ta_all * 0.05, 2); tax_all = round(ta_all * 0.02, 2)
    diff_all = round(adv_all - tdyn_all, 2)
    rem_all = round(res_all - srv_all - tax_all - tplat_all - tdyn_all, 2)

    gvals = [fm(v) for v in g_all]
    gvals += [fm(v) for v in dyn_all]
    gvals += [fm(v) for v in a_all]
    gvals += [fm(adv_all), fm(adv_all), fm(res_all), fm(srv_all), fm(tplat_all), fm(tdyn_all), fm(diff_all), fm(tax_all)]
    cls_l = "negative" if rem_all < 0 else ""
    gvals += [fm(rem_all)]

    tds2 = '<td class="label">合 计</td>'
    for vi, v in enumerate(gvals):
        ec = "highlight " + cls_l if vi == len(gvals) - 1 else "highlight"
        tds2 += '<td class="' + ec + '">' + v + '</td>'
    tds2 += '<td></td>'
    rows += '<tr class="row-total">' + tds2 + '</tr>\n'

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>斌立科技 - 玩具垫资项目（4-5月汇总）</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 20px; color: #1a1a1a; }
.container { max-width: 100%; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }
.title { padding: 16px 24px; font-size: 16px; font-weight: 700; border-bottom: 1px solid #e8e8e8; background: #fafafa; }
.title span { color: #1677ff; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; min-width: 2300px; }
thead th { background: #3c3c3c; color: #fff; font-weight: 600; padding: 8px 6px; text-align: center; white-space: nowrap; border-right: 1px solid #555; font-size: 11.5px; }
thead th:last-child { border-right: none; }
thead th.sub { background: #4a4a4a; font-weight: 500; font-size: 11px; color: #ccc; padding: 5px 6px; }
thead th.group { background: #2c2c2c; }
tbody td { padding: 8px 6px; text-align: center; border-bottom: 1px solid #eee; white-space: nowrap; }
tbody tr.row-apr { background: #fafbfc; }
tbody tr.row-may { background: #fff; }
tbody tr.row-total { background: #f5f5f5; font-weight: 700; border-top: 2px solid #d9d9d9; }
tbody tr:hover { background: #e6f4ff; }
td.label { text-align: left; font-weight: 600; padding-left: 10px; }
td.negative { color: #cf1322; font-weight: 700; }
td.highlight { color: #1677ff; font-weight: 600; }
.note { padding: 12px 24px; font-size: 12px; color: #888; border-top: 1px solid #e8e8e8; background: #fafafa; line-height: 1.6; }
</style>
</head>
<body>
<div class="container">
<div class="title"><span>斌立科技</span> \u2014 玩具垫资项目 \u00b7 4-5月经营汇总</div>
<div class="table-wrap">
<table>
<thead>
<tr>
<th rowspan="2">日期</th>
<th colspan="3" class="group">成交</th>
<th colspan="3" class="group">退款金额</th>
<th colspan="3" class="group">实际成交</th>
<th rowspan="2">90%应付</th>
<th rowspan="2">实际垫付90%</th>
<th rowspan="2">尾款10%</th>
<th rowspan="2">服务费5%</th>
<th rowspan="2">平台技术费</th>
<th rowspan="2">动账支出</th>
<th rowspan="2">垫付差额</th>
<th rowspan="2">税点2%</th>
<th rowspan="2">剩余尾款</th>
<th rowspan="2">状态</th>
</tr>
<tr>
<th class="sub">店6</th><th class="sub">店7</th><th class="sub">店8</th>
<th class="sub">店6</th><th class="sub">店7</th><th class="sub">店8</th>
<th class="sub">店6</th><th class="sub">店7</th><th class="sub">店8</th>
</tr>
</thead>
<tbody>
""" + rows + """
</tbody>
</table>
</div>
<div class="note">
<strong>计算规则：</strong><br>
成交 = 订单CSV商品数量 x 商品金额<br>
退款金额 = 动账CSV出账(排除保证金)<br>
实际成交 = 成交 - 已关闭订单<br>
90%应付 = 实际成交 x 0.9<br>
尾款10% = 实际成交 x 0.1<br>
服务费5% = 实际成交 x 0.05<br>
税点2% = 实际成交 x 0.02<br>
平台技术费 = 结算CSV支出合计<br>
动账支出 = 动账CSV出账(排除保证金)<br>
垫付差额 = 90%应付 - 动账支出<br>
剩余尾款 = 尾款10% - 服务费5% - 税点2% - 平台技术费 - 动账支出<br>
<span style="color:#cf1322">红色</span>为负数 <span style="color:#1677ff">蓝色</span>为合计行
</div>
</div>
</body>
</html>"""

    out_path = os.path.join(output_dir, "垫资结算汇总表.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved: %s" % out_path)

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    out = sys.argv[2] if len(sys.argv) > 2 else base
    gen_html(base, out)
