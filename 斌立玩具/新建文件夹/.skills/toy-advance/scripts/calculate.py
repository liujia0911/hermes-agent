import csv, sys, os
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

def calc(account_dir):
    order_file = os.path.join(account_dir, "订单.csv")
    dynamic_file = None
    settle_files = []
    for f in os.listdir(account_dir):
        fp = os.path.join(account_dir, f)
        if not f.endswith(".csv"): continue
        if "动账" in f: dynamic_file = fp
        elif "结算" in f: settle_files.append(fp)
    for label, path in [("订单",order_file),("动账",dynamic_file)]:
        if not os.path.exists(path):
            print("Error: missing %s" % label); sys.exit(1)
    if not settle_files:
        print("Error: no settle files"); sys.exit(1)

    total_gross = 0.0; total_closed = 0.0
    with open(order_file, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        qty_col, amount_col, status_col = find_cols(headers)
        for row in reader:
            try:
                qty = int(row[qty_col]) if row[qty_col] else 0
                amount = float(row[amount_col]) if row[amount_col] else 0.0
                status = row[status_col].strip()
                line = qty * amount
                total_gross += line
                if status == "已关闭": total_closed += line
            except (IndexError, ValueError): continue
    actual_sales = total_gross - total_closed

    total_platform_exp = 0.0
    settle_detail = {}
    platform_detail = {
        "平台服务费": 0.0, "达人佣金": 0.0, "服务商佣金": 0.0,
        "渠道分成": 0.0, "招商服务费": 0.0, "站外推广费": 0.0, "其他分成": 0.0,
    }
    col_map = {32: "平台服务费", 33: "达人佣金", 34: "服务商佣金",
               35: "渠道分成", 36: "招商服务费", 37: "站外推广费", 38: "其他分成"}
    for sf in sorted(settle_files):
        exp_sum = 0.0
        with open(sf, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader); next(reader)
            for row in reader:
                try:
                    if len(row) > 40 and row[40]:
                        exp_sum += float(row[40])
                    for ci, key in col_map.items():
                        if len(row) > ci and row[ci]:
                            platform_detail[key] += float(row[ci])
                except (ValueError, IndexError): continue
        total_platform_exp += exp_sum
        settle_detail[os.path.basename(sf)] = exp_sum

    total_dynamic_out = 0.0
    excluded = []
    with open(dynamic_file, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if not row[0] or not row[0].strip(): continue
            if row[2].strip() != "出账": continue
            try: amount = float(row[3])
            except: continue
            scenario = row[5].strip() if len(row) > 5 else ""
            remark = row[38].strip() if len(row) > 38 and row[38] else ""
            is_deposit = ("保证金" in scenario or "保证金" in remark)
            if is_deposit and abs(amount) >= 100:
                excluded.append((row[0], amount, scenario))
                continue
            total_dynamic_out += amount

    advance_90 = actual_sales * 0.9
    reserve_10 = actual_sales * 0.1
    service_fee_5 = actual_sales * 0.05
    tax_2 = actual_sales * 0.02
    exp_total = abs(total_platform_exp)
    remaining = reserve_10 - service_fee_5 - tax_2 - exp_total - total_dynamic_out

    name = os.path.basename(account_dir.rstrip("/\\"))
    sep = "=" * 60
    print(sep)
    print("  %s" % name)
    print(sep)
    items = [
        ("1. 总成交额", total_gross),
        ("2. 已关闭订单金额", total_closed),
        ("3. 实际成交额", actual_sales),
        ("4. 需垫款90%", advance_90),
        ("5. 尾款10%", reserve_10),
        ("6. 服务费5%", service_fee_5),
        ("7. 税点2%", tax_2),
        ("8. 平台服务费", exp_total),
        ("9. 动账出账合计", total_dynamic_out),
        ("10.剩余尾款", remaining),
    ]
    for label, val in items:
        print("%-30s %12.2f" % (label, val))
    for sf, val in settle_detail.items():
        print("  +- %s %20.2f" % (sf, val))
    has_detail = any(v != 0 for v in platform_detail.values())
    if has_detail:
        print("  +- 明细:")
        for k, v in platform_detail.items():
            if v != 0:
                print("       %s %15.2f" % (k, v))
    if excluded:
        print("  +- 已排除保证金(%d笔):" % len(excluded))
        for dt, amt, sc in excluded:
            print("       %s %9.2f  %s" % (dt, amt, sc))
    print(sep)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calculate.py <dir>")
        sys.exit(1)
    calc(sys.argv[1])
