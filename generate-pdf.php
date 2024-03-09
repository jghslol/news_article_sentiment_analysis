<?php

require __DIR__ . "/vendor/autoload.php";

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->setChroot(__DIR__);
$options->setIsRemoteEnabled(true);
$dompdf = new Dompdf($options);

$python = shell_exec("python main.py");

$path = "scraped_data.json";

$jsonString = file_get_contents($path);

$data = json_decode($jsonString, true);

$type = gettype($python);

$python = $type;

$status_of_boxes = [];

if (filter_has_var(INPUT_POST, "guardian")) {
    $check_guardian_box = "True";
} else {
    $check_guardian_box = "False";
}

if (filter_has_var(INPUT_POST, "mail")) {
    $check_mail_box = "True";
} else {
    $check_mail_box = "False";
}

if (filter_has_var(INPUT_POST, "metro")) {
    $check_metro_box = "True";
} else {
    $check_metro_box = "False";
}

$status_of_boxes["guardian"] = $check_guardian_box;
$status_of_boxes["mail"] = $check_mail_box;
$status_of_boxes["metro"] = $check_metro_box;

$html = file_get_contents("template.html");

function get_html_data($data, $newspaper, $newspaper_name) {
    $line = "";
    foreach ($data as $d) {
        if ($d["newspaper"] == $newspaper) {
            $title = $d["summary_title"];
            $title_sentiment_overall = $d["sentiment_title"];
            $title_sentiment_scores = $d["sentiment_title_scores"];
            $article_sentiment_overall = $d["sentiment_analysis_article"];
            $article_sentiment_scores = $d["article_sentiment_overall"];
            $article = $d["salient_sentences"];

            $line_add = "<tr> <td>$newspaper_name</td><td>$title</td><td>$title_sentiment_scores<br><br>$title_sentiment_overall</td><td>$article</td><td>$article_sentiment_overall<br><br>$article_sentiment_scores</td> </tr>";

            $line = $line . $line_add;
        }
    }
    return $line;
}

echo $check_guardian_box;

foreach ($status_of_boxes as $newspaper => $status) {

    if ($status == "True") {
        if ($newspaper == "guardian") {
            $newspaper_name = "The Guardian";
            $html_lines = get_html_data($data, $newspaper, $newspaper_name);
            $html = str_replace("{{ $newspaper }}", $html_lines, $html);
        }

        if ($newspaper == "mail") {
            $newspaper_name = "The Daily Mail";
            $html_lines = get_html_data($data, $newspaper, $newspaper_name);
            $html = str_replace("{{ $newspaper }}", $html_lines, $html);
        }

        if ($newspaper == "metro") {
            $newspaper_name = "Metro";
            $html_lines = get_html_data($data, $newspaper, $newspaper_name);
            $html = str_replace("{{ $newspaper }}", $html_lines, $html);
        }
    }
}

$date_today = date("Y/m/d");

$html = str_replace("{{ date }}", $date_today, $html);

$dompdf->load_html($html);

$dompdf->render();

$dompdf->stream("sentiment_analysis.pdf", ["Attachment" => 0]);

$output = $dompdf->output();
file_put_contents("output.pdf", $output);

?>
