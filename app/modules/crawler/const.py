DATA_API: str = "api.bilibili.com/x/space/wbi/arc/search"
SPACE_PAGE_URL: str = r"https://space.bilibili.com/{}/video"
XPATH: str = (
    # "//*[text()='下一页' and (not(@disabled) or not(contains(@class, 'disabled')))]"
    "//li[@title='下一页' and (not(@disabled) and not(contains(@class, 'disabled')))]"
)
TOTAL_PAGE_XPATH: str = "//span[contains(@class, 'total')]"
VIDEO_URL: str = "https://www.bilibili.com/video/{}/"
