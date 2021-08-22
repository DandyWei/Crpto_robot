//@version=4
study("Engulfing - Bullish", shorttitle = "Engulfing - Bull", overlay=true)

C_DownTrend = true
C_UpTrend = true
var trendRule1 = "SMA50"
var trendRule2 = "SMA50, SMA200"
var trendRule = input(trendRule1, "Detect Trend Based On", options=[trendRule1, trendRule2, "No detection"])

if trendRule == trendRule1
	priceAvg = sma(close, 50)
	C_DownTrend := close < priceAvg
	C_UpTrend := close > priceAvg

if trendRule == trendRule2
	sma200 = sma(close, 200)
	sma50 = sma(close, 50)
	C_DownTrend := close < sma50 and sma50 < sma200
	C_UpTrend := close > sma50 and sma50 > sma200
C_Len = 14 // ema depth for bodyAvg
C_ShadowPercent = 5.0 // size of shadows
C_ShadowEqualsPercent = 100.0
C_DojiBodyPercent = 5.0
C_Factor = 2.0 // shows the number of times the shadow dominates the candlestick body

C_BodyHi = max(close, open)
C_BodyLo = min(close, open)
C_Body = C_BodyHi - C_BodyLo
C_BodyAvg = ema(C_Body, C_Len)
C_SmallBody = C_Body < C_BodyAvg
C_LongBody = C_Body > C_BodyAvg
C_UpShadow = high - C_BodyHi
C_DnShadow = C_BodyLo - low
C_HasUpShadow = C_UpShadow > C_ShadowPercent / 100 * C_Body
C_HasDnShadow = C_DnShadow > C_ShadowPercent / 100 * C_Body
C_WhiteBody = open < close
C_BlackBody = open > close
C_Range = high-low
C_IsInsideBar = C_BodyHi[1] > C_BodyHi and C_BodyLo[1] < C_BodyLo
C_BodyMiddle = C_Body / 2 + C_BodyLo
C_ShadowEquals = C_UpShadow == C_DnShadow or (abs(C_UpShadow - C_DnShadow) / C_DnShadow * 100) < C_ShadowEqualsPercent and (abs(C_DnShadow - C_UpShadow) / C_UpShadow * 100) < C_ShadowEqualsPercent
C_IsDojiBody = C_Range > 0 and C_Body <= C_Range * C_DojiBodyPercent / 100
C_Doji = C_IsDojiBody and C_ShadowEquals

patternLabelPosLow = low - (atr(30) * 0.6)
patternLabelPosHigh = high + (atr(30) * 0.6)
//標記位置
label_color_bullish = input(color.blue, "Label Color Bullish")
//包兩根
C_EngulfingBullishNumberOfCandles = 2
C_EngulfingBullish = C_DownTrend and C_WhiteBody and C_LongBody and C_BlackBody[1] and C_SmallBody[1]
												and close >= open[1] and open <= close[1] and ( close > open[1] or open < close[1] )
alertcondition(C_EngulfingBullish, title = "New pattern detected", message = "New Engulfing – Bullish pattern detected")
if C_EngulfingBullish
    var ttBullishEngulfing = "Engulfing\nAt the end of a given downward trend, there will mos" + /
		"t likely be a reversal pattern. To distinguish the first day, this candlestick pattern uses a" + /
		" small body, followed by a day where the candle body fully overtakes the body from the day before, a"+ /
		"nd closes in the trend’s opposite direction. Although similar to the outside reversal chart pattern, it i"+/
		"s not essential for this pattern to completely overtake the range (high to low), rather only"+/
		" the open and the close."
    label.new(bar_index, patternLabelPosLow, text="BE", style=label.style_label_up, color = label_color_bullish, textcolor=color.white, tooltip = ttBullishEngulfing)
bgcolor(highest(C_EngulfingBullish?1:0, C_EngulfingBullishNumberOfCandles)!=0 ? color.blue : na, offset=-(C_EngulfingBullishNumberOfCandles-1))
