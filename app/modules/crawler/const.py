
DATA_API: str = "api.bilibili.com/x/space/wbi/arc/search"
SPACE_PAGE_URL: str = r"https://space.bilibili.com/{}/video"
XPATH: str = (
    "//*[text()='下一页' and (not(@disabled) or not(contains(@class, 'disabled')))]"
)
VIDEO_URL: str = "https://www.bilibili.com/video/{}/"