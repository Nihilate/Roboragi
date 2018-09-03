/**
 * Vsts test coverage view doesn't load external CSS due to security reasons.
 * So we are converting all external css files to internal <style> tags using vsts-coverage-styles (node module).
 * Fix all UI issues due to VSTS stripping :after & :before selectors, images & charsets
 */
const vstsCoverageStyles = require('vsts-coverage-styles').VstsCoverageStyles;
const overrideCss = '.status-line { clear:both;} ' +
    '.coverage .line-count, .coverage .line-coverage, ' +
    '.coverage .text .prettyprint {font-size:12px !important; ' +
    'line-height:1.2 !important;font-family:Consolas, "Liberation Mono", Menlo, Courier, monospace !important;}' +
    '.coverage .line-count{max-width:40px;padding-right:25px !important;} ' +
    '.coverage .line-coverage{max-width:45px;}' +
    '.coverage .line-coverage .cline-any{padding-right:25px !important;}' +
    '.coverage-summary{font-size:small;}';

// Default Options
vstsCoverageStyles({
    coverageDir: './htmlcov',
    pattern: '/**/*.html',
    fileEncoding: 'utf8',
    minifyOptions: {
    },
    extraCss: overrideCss,
    preProcessFn: function (html) {
        return html.replace(new RegExp('×', 'g'), 'x');
    },
    postProcessFn: function(html) {
        return html;
    }
});