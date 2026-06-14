$retry = 3
while ($retry--) {
    cd E:\oberjet\daily-ai-news
    git pull
    if ($?) { break }
    Start-Sleep 15
}

# 推送日报到飞书
$today = (Get-Date).ToString("yyyy-MM-dd")
$newsFile = "news/$today-AI资讯日报.md"
if (Test-Path $newsFile) {
    lark-cli im +messages-send --chat-id oc_528eab65e04bd1bf36d7592f07464f46 --text "🤖 AI 资讯日报 — $today 已更新

📄 https://github.com/itoe558/daily-ai-news/blob/master/news/$today-AI资讯日报.md"
}
