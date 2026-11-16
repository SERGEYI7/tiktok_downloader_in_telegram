package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"

	// "html"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/cdproto/network"
	"github.com/chromedp/chromedp"
)

type Page struct {
	Scope struct {
		Detail struct {
			ItemInfo struct {
				ItemStruct struct {
					Video struct {
						PlayAddr     string `json:"playAddr"`
						DownloadAddr string `json:"downloadAddr"`
					} `json:"video"`
				} `json:"itemStruct"`
			} `json:"itemInfo"`
		} `json:"webapp.video-detail"`
	} `json:"__DEFAULT_SCOPE__"`
}

// download скачивает videoURL в path. Использует cookies и User-Agent
// браузера из ctx, поэтому вызывать нужно, пока браузер ещё открыт.
func download(ctx context.Context, videoURL, path string) error {
	ck, err := chromedp.Call(ctx, network.GetCookies, network.GetCookiesParams{})
	if err != nil {
		return err
	}
	var parts []string
	for _, c := range ck.Cookies {
		parts = append(parts, c.Name+"="+c.Value)
	}
	ua, err := chromedp.Run(ctx, chromedp.Evaluate[string](`navigator.userAgent`))
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, videoURL, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Cookie", strings.Join(parts, "; "))
	req.Header.Set("Referer", "https://www.tiktok.com/")
	req.Header.Set("User-Agent", ua)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("скачивание: %s", resp.Status)
	}

	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, resp.Body)
	return err
}

func main() {
	ctx, cancel := chromedp.NewContext(context.Background())
	defer cancel()
	// if err != nil {
	// 	panic(err)
	// }

	if err := chromedp.Do(ctx, chromedp.Navigate("https://vt.tiktok.com/ZSpbDG2Ab/")); err != nil {
		panic("error navigate")
	}

	res, err := chromedp.Run(ctx, chromedp.OuterHTML(`html`))
	if err != nil {
		panic(err)
	}

	doc, err := goquery.NewDocumentFromReader(strings.NewReader(res))
	if err != nil {
		panic(err)
	}

	var data Page
	find_rehydration := doc.Find("#__UNIVERSAL_DATA_FOR_REHYDRATION__").Text()
	err = json.Unmarshal([]byte(find_rehydration), &data)
	if err != nil {
		fmt.Println("Ничего нет???? ", find_rehydration)
		panic(err)
	}

	fmt.Println(data.Scope.Detail.ItemInfo.ItemStruct.Video.PlayAddr)

	v := data.Scope.Detail.ItemInfo.ItemStruct.Video
	if err := download(ctx, v.PlayAddr, "video.mp4"); err != nil {
		panic(err)
	}

	// if !json.Valid([]byte(res)) {
	// 	panic("Не то взял")
	// }

	buf, err := chromedp.Run(ctx, chromedp.CaptureScreenshot())
	if err != nil {
		panic(err)
	}

	os.WriteFile("probe.png", buf, 0o777)

	fmt.Println("Готово")
}
